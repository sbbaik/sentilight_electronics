from __future__ import annotations

import argparse
import importlib.util
import json
from collections import OrderedDict
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


SYSTEM_PROMPT = (
    "당신은 감정 기반 스마트 조명 제어 모델입니다. "
    "반드시 JSON만 출력하세요. "
    "규칙: 명시적 색상 요청이 있으면 hue는 그 색상을 우선합니다. "
    "감정은 saturation, brightness, dimmer, color temperature에 반영하세요. "
    "애매한 감정이면 안전하고 무난한 조명값을 사용하세요. "
    "출력 키는 H,S,B,Dimmer,CT만 사용하세요."
)
USER_PROMPT_TEMPLATE = "문장: {text}"
REQUIRED_FIELDS = ("H", "S", "B", "Dimmer", "CT")
FIELD_RANGES = {
    "H": (0, 360),
    "S": (0, 100),
    "B": (0, 100),
    "Dimmer": (0, 100),
    "CT": (153, 500),  # W5: matches the declared prompt range
}


@dataclass
class RuntimeModel:
    torch: Any
    model: Any
    tokenizer: Any
    device: Any
    max_new_tokens: int
    eos_id: Optional[int]
    model_dir: Path
    checkpoint_path: Path
    quantization: dict[str, Any]


def _load_definition(model_dir: Path):
    definition_path = model_dir / "model_definition.py"
    spec = importlib.util.spec_from_file_location("sentilight_compactlm_definition", definition_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import model definition: {definition_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _clean_state_key(key: str) -> str:
    return key.removeprefix("module.").removeprefix("_orig_mod.")


def _extract_state_dict(checkpoint: Any) -> dict[str, Any]:
    if not isinstance(checkpoint, dict):
        raise RuntimeError("CompactLM checkpoint must be a dictionary")
    state = checkpoint.get("model_state_dict") or checkpoint.get("state_dict") or checkpoint.get("model") or checkpoint
    cleaned = OrderedDict(
        (_clean_state_key(key), value)
        for key, value in state.items()
    )
    if hasattr(state, "_metadata"):
        cleaned._metadata = {
            _clean_state_key(key): value
            for key, value in state._metadata.items()
        }
    return cleaned


def _unpack_4bit_codes(torch_mod: Any, packed: Any, total_values: int) -> Any:
    packed_flat = packed.reshape(-1).to(torch_mod.int16)
    unpacked = torch_mod.empty(packed_flat.numel() * 2, dtype=torch_mod.uint8)
    unpacked[0::2] = (packed_flat & 0x0F).to(torch_mod.uint8)
    unpacked[1::2] = ((packed_flat >> 4) & 0x0F).to(torch_mod.uint8)
    return unpacked[:total_values]


def _dequantize_grouped_weight(torch_mod: Any, entry: dict[str, Any]) -> Any:
    bits = int(entry["bits"])
    shape = tuple(int(value) for value in entry["shape"])
    if len(shape) != 2:
        raise RuntimeError(f"Mixed-bit CompactLM weight must be 2D, got shape={shape}")

    rows, cols = shape
    group_size = int(entry.get("group_size", 64))
    groups = (cols + group_size - 1) // group_size
    total_values = rows * groups * group_size

    if bits == 4 and "packed" in entry:
        codes = _unpack_4bit_codes(torch_mod, entry["packed"], total_values)
    else:
        codes = entry["codes"].reshape(-1).to(torch_mod.uint8)[:total_values]

    offset = 1 << (bits - 1)
    signed = codes.to(torch_mod.int16) - offset
    signed = signed.to(torch_mod.float32).view(rows, groups, group_size)
    scales = entry["scales"].to(torch_mod.float32).view(rows, groups, 1)
    weight = (signed * scales).reshape(rows, groups * group_size)[:, :cols]
    return weight.contiguous()


def _materialize_mixed_bit_state_dict(checkpoint: Any, torch_mod: Any) -> dict[str, Any]:
    if not isinstance(checkpoint, dict):
        raise RuntimeError("Mixed-bit CompactLM checkpoint must be a dictionary")

    base_state = checkpoint.get("model_state_dict") or {}
    if not isinstance(base_state, dict):
        raise RuntimeError("Mixed-bit CompactLM model_state_dict must be a dictionary")

    state = OrderedDict((_clean_state_key(key), value) for key, value in base_state.items())
    quantized_state = checkpoint.get("quantized_state_dict") or {}
    if not isinstance(quantized_state, dict) or not quantized_state:
        raise RuntimeError("Mixed-bit CompactLM checkpoint has no quantized_state_dict")

    for key, entry in quantized_state.items():
        if not isinstance(entry, dict):
            raise RuntimeError(f"Invalid mixed-bit entry for {key}")
        state[_clean_state_key(key)] = _dequantize_grouped_weight(torch_mod, entry)

    return state


def _find_tokenizer(model_dir: Path, tokenizer_dir: str | None) -> Path:
    base = model_dir / tokenizer_dir if tokenizer_dir else model_dir / "tokenizer"
    candidates = [base / "tokenizer.json", model_dir / "tokenizer.json"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"tokenizer.json not found under {base}")


def _resolve_eos_id(tokenizer: Any) -> Optional[int]:
    for token in ("<eos>", "</s>"):
        token_id = tokenizer.token_to_id(token)
        if token_id is not None:
            return int(token_id)
    return None


def _normalize_json_object(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError("CompactLM JSON output must be an object")

    normalized: dict[str, int] = {}
    for field in REQUIRED_FIELDS:
        if field not in value:
            raise ValueError(f"Missing required field: {field}")
        raw_value = value[field]
        if isinstance(raw_value, bool):
            raise ValueError(f"Field {field} must be numeric, got bool")
        if not isinstance(raw_value, (int, float)):
            raise ValueError(f"Field {field} must be numeric")
        int_value = int(round(float(raw_value)))
        lower, upper = FIELD_RANGES[field]
        if not (lower <= int_value <= upper):
            raise ValueError(f"Field {field} out of range: {int_value}")
        normalized[field] = int_value

    return normalized


def _try_parse_completed_json(text: str) -> Optional[dict[str, int]]:
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        ch = text[idx]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : idx + 1]
                try:
                    return _normalize_json_object(json.loads(candidate))
                except (json.JSONDecodeError, ValueError):
                    return None

    return None


def _extract_json(text: str) -> dict[str, int]:
    parsed = _try_parse_completed_json(text)
    if parsed is None:
        raise ValueError(f"CompactLM did not generate a valid control JSON: {text[:300]}")
    return parsed


def build_prompt(text: str) -> str:
    stripped = text.strip()
    if "<|system|>" in stripped or "<|user|>" in stripped:
        return stripped
    return (
        "<|system|>\n"
        f"{SYSTEM_PROMPT}\n"
        "<|user|>\n"
        f"{USER_PROMPT_TEMPLATE.format(text=stripped)}\n"
        "<|assistant|>\n"
    )


def load_model(config) -> RuntimeModel:
    try:
        import torch
        from tokenizers import Tokenizer
    except ImportError as exc:
        raise RuntimeError("CompactLM requires torch and tokenizers") from exc

    model_dir = Path(config.resolved_model_dir)
    checkpoint_path = model_dir / str(config.checkpoint)
    tokenizer_path = _find_tokenizer(model_dir, config.tokenizer_dir)
    options = config.options or {}

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    definition = _load_definition(model_dir)
    config_data = checkpoint.get("model_config") or checkpoint.get("config") or checkpoint.get("cfg") or {}
    model_config = definition.ModelConfig(**config_data)
    quantization = checkpoint.get("quantization", {})
    format_name = str(checkpoint.get("format", ""))

    model = definition.SentilightCompactLM(model_config)
    is_mixed4 = quantization.get("method") == "mixed4_weightonly_loadtime_dequant" or "mixed4" in format_name
    if quantization.get("method") == "dynamic_int8" or "int8" in format_name:
        model = definition.quantize_conservative_int8(model)

    state_dict = (
        _materialize_mixed_bit_state_dict(checkpoint, torch)
        if is_mixed4
        else _extract_state_dict(checkpoint)
    )
    model.load_state_dict(state_dict, strict=True)

    requested_device = str(options.get("device", "cpu"))
    if quantization.get("method") == "dynamic_int8" and requested_device != "cpu":
        raise RuntimeError("Dynamic INT8 CompactLM is CPU-only in this environment.")

    device = torch.device(requested_device)
    model.to(device).eval()
    tokenizer = Tokenizer.from_file(str(tokenizer_path))

    return RuntimeModel(
        torch=torch,
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_new_tokens=int(options.get("max_new_tokens", 96)),
        eos_id=_resolve_eos_id(tokenizer),
        model_dir=model_dir,
        checkpoint_path=checkpoint_path,
        quantization=quantization,
    )


def _select_next_id(torch_mod: Any, logits: Any, temperature: float, top_k: Optional[int]) -> Any:
    if temperature <= 0:
        return torch_mod.argmax(logits, dim=-1, keepdim=True)

    logits = logits / temperature
    if top_k is not None and top_k > 0:
        values, _ = torch_mod.topk(logits, k=min(top_k, logits.size(-1)))
        cutoff = values[:, [-1]]
        logits = torch_mod.where(
            logits < cutoff,
            torch_mod.full_like(logits, -float("inf")),
            logits,
        )

    probs = torch_mod.softmax(logits, dim=-1)
    return torch_mod.multinomial(probs, num_samples=1)


def generate_json(
    text: str,
    runtime: RuntimeModel,
    *,
    temperature: float = 0.0,
    top_k: Optional[int] = None,
    use_kv_cache: bool = True,
    use_last_logits_only: bool = True,
    max_new_tokens: Optional[int] = None,
) -> tuple[dict[str, int], dict[str, Any]]:
    torch_mod = runtime.torch
    prompt_text = build_prompt(text)
    encoded = runtime.tokenizer.encode(prompt_text)
    prompt_ids = encoded.ids[-runtime.model.cfg.block_size :]
    idx = torch_mod.tensor([prompt_ids], dtype=torch_mod.long, device=runtime.device)
    max_steps = runtime.max_new_tokens if max_new_tokens is None else int(max_new_tokens)

    generated_ids: list[int] = []
    decoded_text = ""
    past_kv = None
    peak_rss_bytes = None

    try:
        import psutil

        process = psutil.Process()

        def sample_rss() -> None:
            nonlocal peak_rss_bytes
            rss = process.memory_info().rss
            peak_rss_bytes = rss if peak_rss_bytes is None else max(peak_rss_bytes, rss)

    except Exception:
        process = None

        def sample_rss() -> None:
            return None

    with torch_mod.inference_mode():
        for _ in range(max_steps):
            if use_kv_cache:
                current_idx = idx if past_kv is None else idx[:, -1:]
                logits, past_kv = runtime.model.forward_inference(
                    current_idx,
                    past_kv=past_kv,
                    use_cache=True,
                )
            else:
                current_idx = idx[:, -runtime.model.cfg.block_size :]
                if use_last_logits_only:
                    logits, _ = runtime.model.forward_inference(
                        current_idx,
                        past_kv=None,
                        use_cache=False,
                    )
                else:
                    full_logits, _ = runtime.model(current_idx)
                    logits = full_logits[:, -1, :]

            next_id = _select_next_id(torch_mod, logits, temperature=temperature, top_k=top_k)
            next_token = int(next_id.item())
            idx = torch_mod.cat([idx, next_id], dim=1)
            generated_ids.append(next_token)
            sample_rss()

            if runtime.eos_id is not None and next_token == runtime.eos_id:
                break

            decoded_text = runtime.tokenizer.decode(generated_ids, skip_special_tokens=True)
            completed = _try_parse_completed_json(decoded_text)
            if completed is not None:
                return completed, {
                    "generated_ids": generated_ids,
                    "generated_text": decoded_text,
                    "prompt_text": prompt_text,
                    "peak_rss_bytes": peak_rss_bytes,
                    "used_kv_cache": use_kv_cache,
                    "used_last_logits_only": use_last_logits_only,
                }

    decoded_text = runtime.tokenizer.decode(generated_ids, skip_special_tokens=True)
    return _extract_json(decoded_text), {
        "generated_ids": generated_ids,
        "generated_text": decoded_text,
        "prompt_text": prompt_text,
        "peak_rss_bytes": peak_rss_bytes,
        "used_kv_cache": use_kv_cache,
        "used_last_logits_only": use_last_logits_only,
    }


def predict(text: str, runtime: RuntimeModel) -> dict[str, int]:
    result, _ = generate_json(
        text,
        runtime,
        temperature=0.0,
        top_k=None,
        use_kv_cache=True,
        use_last_logits_only=True,
    )
    return result


def _parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _build_config(model_dir: Path, checkpoint: Optional[str], device: str, max_new_tokens: int):
    config_data = _parse_simple_yaml(model_dir / "model_config.yaml")
    return type(
        "Config",
        (),
        {
            "resolved_model_dir": str(model_dir),
            "checkpoint": checkpoint or config_data["checkpoint"],
            "tokenizer_dir": config_data.get("tokenizer_dir", "tokenizer"),
            "options": {
                "device": device,
                "max_new_tokens": max_new_tokens,
            },
        },
    )()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CompactLM Q4 inference for a single prompt.")
    parser.add_argument("--text", required=True, help="Input text prompt")
    parser.add_argument("--model-dir", default=Path(__file__).resolve().parent, type=Path)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-new-tokens", default=48, type=int)
    parser.add_argument("--temperature", default=0.0, type=float)
    parser.add_argument("--top-k", default=None, type=int)
    parser.add_argument("--disable-kv-cache", action="store_true")
    parser.add_argument("--disable-last-logits", action="store_true")
    parser.add_argument("--show-generated-text", action="store_true")
    args = parser.parse_args()

    runtime = load_model(
        _build_config(
            model_dir=args.model_dir.resolve(),
            checkpoint=args.checkpoint,
            device=args.device,
            max_new_tokens=args.max_new_tokens,
        )
    )
    result, metadata = generate_json(
        args.text,
        runtime,
        temperature=args.temperature,
        top_k=args.top_k,
        use_kv_cache=not args.disable_kv_cache,
        use_last_logits_only=not args.disable_last_logits,
    )
    print(json.dumps(result, ensure_ascii=False))
    if args.show_generated_text:
        print(metadata["generated_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
