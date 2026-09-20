"""Deployment-facing summary of candidate configurations across all available seeds.

For each run family: parameters, weights-only checkpoint size (fp32 bytes = params × 4) and the
mixed-4/6/8-bit export size when present, exact / coarse / strict mean ± SD over seeds, invalid-JSON
rate, mean and p95 latency (reference 96-step decoder, no KV cache), and speed ratio vs the deployed
configuration (W384).

Usage: python tools/final_model_table.py --out backend/reports/scale_grid_combo/final_model_table
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics as st
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIMS = ("H", "S", "B", "Dimmer", "CT")
FAMILIES = {
    "W384 (deployed cfg: d384 L8 V24k-prod)": "backend/reports/scale_grid_width/run_summaries/compactlm_W384_f100_s*.json",
    "D4 (d384 L4 V24k-prod)": "backend/reports/scale_grid_depth/run_summaries/compactlm_D4_f100_s*.json",
    "V2 V4k (d384 L8 V4k-natural)": "backend/reports/scale_grid_vocab_natural/V4k/run_summaries/compactlm_V4k_f100_s*.json",
    "C4kL4 (d384 L4 V4k-natural)": "backend/reports/scale_grid_combo/run_summaries/compactlm_C4kL4_f100_s*.json",
    "V2 V4k mixed-4/6/8-bit (KV-cache eval runtime)": "backend/reports/scale_grid_vocab_natural_q4/run_summaries/compactlm_V4kq_f100_s*.json",
    "C4kL4 mixed-4/6/8-bit (KV-cache eval runtime)": "backend/reports/scale_grid_combo_q4/run_summaries/compactlm_C4kL4q_f100_s*.json",
}


def exact_rate(per_row: Path) -> float:
    n = ok = 0
    for l in per_row.open(encoding="utf-8"):
        r = json.loads(l); n += 1
        p, ref = r.get("predicted"), r["reference"]
        ok += bool(p) and all(int(p[k]) == int(ref[k]) for k in DIMS)
    return 100 * ok / n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "backend/reports/scale_grid_combo/final_model_table")
    args = ap.parse_args()
    rows = []
    for name, pat in FAMILIES.items():
        files = sorted(glob.glob(str(REPO_ROOT / pat)))
        if not files:
            continue
        ex, co, stc, inval, lat, p95, seeds = [], [], [], [], [], [], []
        params = None
        for f in files:
            j = json.loads(Path(f).read_text(encoding="utf-8")); m = j["metrics"]
            seed = int(re.search(r"_s(\d+)\.json$", f).group(1)); seeds.append(seed)
            params = j["parameter_count"]
            per_row = Path(f).parent.parent / "per_row" / (Path(f).stem + ".jsonl")
            ex.append(exact_rate(per_row) if per_row.exists() else float("nan"))
            co.append(m["coarse_3bin_pass_rate"] * 100); stc.append(m["strict_semantic_pass_rate"] * 100)
            inval.append(100 * m["errors"] / max(1, m["successes"] + m["errors"]))
            lat.append(m["latency"]["mean_ms"]); p95.append(m["latency"]["p95_ms"])
        sd = lambda v: st.stdev(v) if len(v) > 1 else 0.0
        rows.append({"family": name, "seeds": seeds, "n_seeds": len(seeds), "params": params,
                     "fp32_weights_mb": params * 4 / 1e6,
                     "exact_mean": st.mean(ex), "exact_sd": sd(ex), "coarse_mean": st.mean(co), "coarse_sd": sd(co),
                     "strict_mean": st.mean(stc), "strict_sd": sd(stc), "invalid_json_pct": st.mean(inval),
                     "latency_mean_ms": st.mean(lat), "latency_p95_ms": st.mean(p95)})
    # mixed4 export sizes
    q4 = sorted(glob.glob(str(REPO_ROOT / "backend/models/compact_llm/scale_grid_runs_combo_q4/*_mixed4.pt")))
    q4_mb = st.mean(Path(p).stat().st_size for p in q4) / 1e6 if q4 else None
    ref = next((r for r in rows if r["family"].startswith("W384")), None)
    lines = ["# Candidate configurations — deployment-facing summary", "",
             "| Configuration | seeds | params | fp32 weights (MB) | exact % | coarse % | strict % | invalid JSON % | latency mean / p95 (ms) | speed vs deployed |",
             "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for r in rows:
        speed = f"{ref['latency_mean_ms'] / r['latency_mean_ms']:.2f}×" if ref and r["latency_mean_ms"] else "-"
        lines.append(f"| {r['family']} | {r['n_seeds']} | {r['params']:,} | {r['fp32_weights_mb']:.1f} | {r['exact_mean']:.1f} ± {r['exact_sd']:.1f} | "
                     f"{r['coarse_mean']:.1f} ± {r['coarse_sd']:.1f} | {r['strict_mean']:.1f} ± {r['strict_sd']:.1f} | {r['invalid_json_pct']:.2f} | "
                     f"{r['latency_mean_ms']:.0f} / {r['latency_p95_ms']:.0f} | {speed} |")
    if q4_mb:
        lines += ["", f"- Mixed-4/6/8-bit export of C4kL4 (group 64; embedding kept fp32): {q4_mb:.1f} MB on disk vs {rows[-1]['fp32_weights_mb'] if rows else 0:.1f} MB fp32 weights.",
                  "- Latency is the KV-cache-free 96-step reference decoder (IoTJ Tier 1 protocol); the quantized evaluator dequantizes at load time, so its latency is not a quantization speed measurement."]
    args.out.with_suffix(".json").write_text(json.dumps({"rows": rows, "mixed4_export_mb": q4_mb}, ensure_ascii=False, indent=1), encoding="utf-8")
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
