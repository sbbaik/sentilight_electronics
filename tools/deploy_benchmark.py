"""Deployment-side benchmark of one CompactLM checkpoint through the production runtime
(backend/models/compact_llm_q4/inference.py: load-time dequantisation, KV-cache greedy decoding),
on the device the backend actually uses (CPU by default, as in backend/config/models.yaml).

Measures, in a fresh process: load time, model-only inference latency (median / p95 / mean over N
prompts after warm-up), peak RSS, process RSS after load, checkpoint file size, invalid-JSON rate on
the benchmark prompts, and exact/coarse agreement with the reference tuples for those prompts.

Usage (one model per process so peak RSS is attributable):
  python tools/deploy_benchmark.py --checkpoint <pt> --tokenizer-dir <dir> --label <name> \
      --dataset backend/models/compact_llm/datasets/keff_series/K240/test_rule.jsonl --n 300 --device cpu \
      --out backend/reports/deploy_benchmark/<name>.json
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import statistics as st
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT / "backend", REPO_ROOT / "backend" / "models"):
    sys.path.insert(0, str(p))

from common.benchmark_eval import coarse_3bin_pass  # noqa: E402
from compact_llm_q4.inference import load_model, predict  # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")


class Cfg:
    def __init__(self, model_dir: Path, checkpoint: Path, tokenizer_dir: str, device: str, max_new_tokens: int):
        self.resolved_model_dir = str(model_dir); self.checkpoint = str(checkpoint); self.tokenizer_dir = tokenizer_dir
        self.options = {"device": device, "max_new_tokens": max_new_tokens}


def rss_mb() -> float:
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    return float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--tokenizer-dir", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--dataset", type=Path, default=REPO_ROOT / "backend/models/compact_llm/datasets/keff_series/K240/test_rule.jsonl")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--warmup", type=int, default=20)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    import torch
    if args.threads:
        torch.set_num_threads(args.threads)
    rows = [json.loads(l) for l in args.dataset.open(encoding="utf-8") if l.strip()]
    # deterministic subset: every k-th row
    step = max(1, len(rows) // (args.n + args.warmup))
    sample = rows[::step][: args.n + args.warmup]
    rss_before = rss_mb()
    t0 = time.perf_counter()
    runtime = load_model(Cfg(REPO_ROOT / "backend" / "models" / "compact_llm_q4", args.checkpoint.resolve(), args.tokenizer_dir, args.device, args.max_new_tokens))
    load_s = time.perf_counter() - t0
    rss_after_load = rss_mb()
    lat, invalid, exact, coarse = [], 0, 0, 0
    for i, r in enumerate(sample):
        t = time.perf_counter()
        try:
            pred = predict(str(r["input"]), runtime)
        except Exception:
            pred = None
        dt = (time.perf_counter() - t) * 1000
        if i < args.warmup:
            continue
        lat.append(dt)
        if not pred or any(k not in pred for k in DIMS):
            invalid += 1; continue
        ref = r["output"]
        exact += all(int(pred[k]) == int(ref[k]) for k in DIMS)
        coarse += coarse_3bin_pass(ref, pred)
    lat.sort(); n = len(lat)
    out = {
        "label": args.label, "checkpoint": str(args.checkpoint), "checkpoint_mb": args.checkpoint.stat().st_size / 1e6,
        "device": args.device, "torch_threads": torch.get_num_threads(), "cpu": os.uname().machine,
        "quantization": getattr(runtime, "quantization", None) or (torch.load(args.checkpoint, map_location="cpu").get("quantization") if args.checkpoint.stat().st_size < 200e6 else None),
        "load_time_s": load_s, "rss_before_load_mb": rss_before, "rss_after_load_mb": rss_after_load,
        "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "n_timed": n, "latency_ms": {"median": lat[n // 2], "p95": lat[int(n * 0.95) - 1], "mean": st.mean(lat), "min": lat[0], "max": lat[-1]},
        "invalid_json_rate": invalid / n, "exact_rate": exact / n, "coarse_rate": coarse / n,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("label", "checkpoint_mb", "load_time_s", "peak_rss_mb", "latency_ms", "invalid_json_rate", "exact_rate", "coarse_rate")}, indent=1))


if __name__ == "__main__":
    main()
