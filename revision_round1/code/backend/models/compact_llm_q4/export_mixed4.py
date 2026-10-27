from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any

import torch


FORMAT = "sentilight_compactlm_mixed4_weightonly_v1"
METHOD = "mixed4_weightonly_loadtime_dequant"
DEFAULT_GROUP_SIZE = 64


def _clean_state_key(key: str) -> str:
    return key.removeprefix("module.").removeprefix("_orig_mod.")


def _extract_state_dict(checkpoint: dict[str, Any]) -> OrderedDict[str, torch.Tensor]:
    state = checkpoint.get("model_state_dict") or checkpoint.get("state_dict") or checkpoint.get("model")
    if not isinstance(state, dict):
        raise RuntimeError("source checkpoint does not contain a model state dict")
    return OrderedDict((_clean_state_key(key), value.detach().cpu()) for key, value in state.items())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _block_index(key: str) -> int | None:
    match = re.match(r"blocks\.(\d+)\.", key)
    return int(match.group(1)) if match else None


def _is_quantizable_weight(key: str, tensor: torch.Tensor) -> bool:
    return (
        tensor.is_floating_point()
        and tensor.dim() == 2
        and key.endswith(".weight")
        and not key.startswith("tok_emb.")
        and not key.startswith("lm_head.")
    )


def _choose_bits(key: str, n_layer: int) -> int:
    block_idx = _block_index(key)
    if block_idx in {0, n_layer - 1}:
        return 8
    if ".ffn.down_proj.weight" in key:
        return 8
    if ".attn.o_proj.weight" in key:
        return 6
    return 4


def _pack_4bit(codes: torch.Tensor) -> torch.Tensor:
    flat = codes.reshape(-1).to(torch.uint8)
    if flat.numel() % 2:
        flat = torch.cat([flat, torch.zeros(1, dtype=torch.uint8)])
    low = flat[0::2]
    high = flat[1::2]
    return (low | (high << 4)).contiguous()


def _quantize_grouped(weight: torch.Tensor, bits: int, group_size: int) -> dict[str, Any]:
    if weight.dim() != 2:
        raise ValueError("only 2D Linear weights are supported")

    weight = weight.detach().cpu().float()
    rows, cols = weight.shape
    groups = (cols + group_size - 1) // group_size
    padded_cols = groups * group_size
    if padded_cols != cols:
        weight = torch.cat([weight, torch.zeros(rows, padded_cols - cols)], dim=1)

    grouped = weight.view(rows, groups, group_size)
    qmax = (1 << (bits - 1)) - 1
    qmin = -(1 << (bits - 1))
    scales = grouped.abs().amax(dim=2).clamp(min=1e-8) / float(qmax)
    quantized = torch.round(grouped / scales.unsqueeze(-1)).clamp(qmin, qmax).to(torch.int16)
    codes = (quantized + (1 << (bits - 1))).to(torch.uint8).contiguous()

    entry: dict[str, Any] = {
        "bits": bits,
        "shape": [rows, cols],
        "group_size": group_size,
        "scales": scales.half().contiguous(),
    }
    if bits == 4:
        entry["packed"] = _pack_4bit(codes)
    else:
        entry["codes"] = codes
    return entry


def export_mixed4(source_checkpoint: Path, output_checkpoint: Path, group_size: int) -> dict[str, Any]:
    checkpoint = torch.load(source_checkpoint, map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise RuntimeError("source checkpoint must be a dictionary")

    model_config = checkpoint.get("model_config") or checkpoint.get("config") or checkpoint.get("cfg") or {}
    n_layer = int(model_config.get("n_layer", 8))
    source_state = _extract_state_dict(checkpoint)

    retained_state: OrderedDict[str, torch.Tensor] = OrderedDict()
    quantized_state: OrderedDict[str, dict[str, Any]] = OrderedDict()
    bit_params: dict[str, int] = {}
    retained_params = 0
    quantized_params = 0

    for key, tensor in source_state.items():
        if _is_quantizable_weight(key, tensor):
            bits = _choose_bits(key, n_layer)
            quantized_state[key] = _quantize_grouped(tensor, bits=bits, group_size=group_size)
            bit_params[str(bits)] = bit_params.get(str(bits), 0) + int(tensor.numel())
            quantized_params += int(tensor.numel())
        else:
            retained_state[key] = tensor.half().contiguous() if tensor.is_floating_point() and tensor.dim() == 2 else tensor
            retained_params += int(tensor.numel()) if hasattr(tensor, "numel") else 0

    quantization = {
        "format": FORMAT,
        "method": METHOD,
        "source_model_id": "compact_llm",
        "target_model_id": "compact_llm_q4",
        "display_name": "CompactLM Q4",
        "group_size": group_size,
        "bit_params": bit_params,
        "retained_params": retained_params,
        "quantized_params": quantized_params,
        "packing": {
            "4bit": "packed_nibbles_uint8",
            "6bit": "uint8_codes",
            "8bit": "uint8_codes",
        },
        "sensitive_policy": {
            "first_and_last_transformer_blocks": 8,
            "ffn_down_proj": 8,
            "attention_o_proj": 6,
            "embedding_and_lm_head": "fp16_checkpoint_fp32_runtime",
            "norms": "fp32",
        },
        "runtime": "loadtime_dequant_to_existing_pytorch_graph",
    }
    output = {
        "format": FORMAT,
        "model_state_dict": retained_state,
        "quantized_state_dict": quantized_state,
        "model_config": model_config,
        "metrics": checkpoint.get("metrics", {}),
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_sha256": _sha256(source_checkpoint),
        "exported_for": "compact_llm_q4",
        "quantization": quantization,
    }

    output_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(output, output_checkpoint)

    return {
        "output_checkpoint": str(output_checkpoint),
        "output_size_bytes": output_checkpoint.stat().st_size,
        "source_checkpoint": str(source_checkpoint),
        "source_checkpoint_sha256": output["source_checkpoint_sha256"],
        "quantization": quantization,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CompactLM FP32 checkpoint to mixed 4-bit CompactLM Q4 artifact.")
    model_dir = Path(__file__).resolve().parent
    backend_dir = model_dir.parents[1]
    parser.add_argument(
        "--source-checkpoint",
        type=Path,
        default=backend_dir / "models" / "compact_llm" / "checkpoint" / "sentilight_compactlm_final.pt",
    )
    parser.add_argument(
        "--output-checkpoint",
        type=Path,
        default=model_dir / "checkpoint" / "sentilight_compactlm_mixed4_inference.pt",
    )
    parser.add_argument("--group-size", type=int, default=DEFAULT_GROUP_SIZE)
    parser.add_argument("--metadata-json", type=Path, default=None)
    args = parser.parse_args()

    metadata = export_mixed4(
        source_checkpoint=args.source_checkpoint.resolve(),
        output_checkpoint=args.output_checkpoint.resolve(),
        group_size=args.group_size,
    )
    metadata_path = args.metadata_json or args.output_checkpoint.with_suffix(".meta.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
