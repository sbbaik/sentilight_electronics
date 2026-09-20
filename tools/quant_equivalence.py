"""FP32 vs mixed-4/6/8-bit equivalence for C4kL4 across seeds (IoTJ VII-A protocol).

Per seed: paired rows, exact McNemar (discordant b/c), difference in pp for exact / coarse / strict.
Pooled over seeds: mean difference, 90% CI from the per-seed differences (t, df = n_seeds-1) and from
the pooled paired rows (normal approx.), TOST against a ±3 pp margin.

Usage: python tools/quant_equivalence.py --seeds 42 43 44 45 46 --out backend/reports/scale_grid_combo_q4/quant_equivalence
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
from math import comb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIMS = ("H", "S", "B", "Dimmer", "CT")
T90 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943}


def rows(p: Path) -> dict[int, tuple[bool, bool, bool]]:
    o = {}
    for l in p.open(encoding="utf-8"):
        r = json.loads(l); pr, ref = r.get("predicted"), r["reference"]
        o[r["row_index"]] = (bool(r["strict"]), bool(r["coarse"]), bool(pr) and all(int(pr[k]) == int(ref[k]) for k in DIMS))
    return o


def mcnemar(a, b, i):
    ks = a.keys() & b.keys()
    bo = sum(1 for k in ks if b[k][i] and not a[k][i]); ao = sum(1 for k in ks if a[k][i] and not b[k][i])
    n, k = bo + ao, min(bo, ao)
    p = min(1.0, 2 * sum(comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1.0
    return bo, ao, p, len(ks)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    ap.add_argument("--margin", type=float, default=3.0)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "backend/reports/scale_grid_combo_q4/quant_equivalence")
    ap.add_argument("--fp32-pattern", default="backend/reports/scale_grid_combo/per_row/compactlm_C4kL4_f100_s{s}.jsonl")
    ap.add_argument("--q4-pattern", default="backend/reports/scale_grid_combo_q4/per_row/compactlm_C4kL4q_f100_s{s}.jsonl")
    ap.add_argument("--label", default="C4kL4")
    args = ap.parse_args()
    fp = lambda s: REPO_ROOT / args.fp32_pattern.format(s=s)
    q4 = lambda s: REPO_ROOT / args.q4_pattern.format(s=s)
    seeds = [s for s in args.seeds if fp(s).exists() and q4(s).exists()]
    out = {"seeds": seeds, "margin_pp": args.margin, "metrics": {}}
    lines = [f"# Quantization equivalence: {args.label} fp32 vs mixed-4/6/8-bit (seeds {seeds}, margin ±{args.margin} pp)", "",
             "| metric | per-seed Δ (q − fp32, pp) | mean Δ | 90% CI (seed-level t) | 90% CI (pooled rows) | McNemar p per seed | TOST |",
             "|---|---|--:|---|---|---|---|"]
    for name, i in (("exact", 2), ("coarse", 1), ("strict", 0)):
        deltas, ps, tot_b, tot_a, tot_n = [], [], 0, 0, 0
        for s in seeds:
            a, b = rows(fp(s)), rows(q4(s))
            bo, ao, p, n = mcnemar(a, b, i)
            deltas.append((bo - ao) / n * 100); ps.append(p); tot_b += bo; tot_a += ao; tot_n += n
        m = st.mean(deltas)
        if len(deltas) > 1:
            se = st.stdev(deltas) / math.sqrt(len(deltas)); ci_t = (m - T90[len(deltas) - 1] * se, m + T90[len(deltas) - 1] * se)
        else:
            ci_t = (float("nan"), float("nan"))
        # pooled paired rows: Δ = (b - a)/N, var ≈ (b + a)/N² (McNemar normal approx.)
        pm = (tot_b - tot_a) / tot_n * 100; pse = math.sqrt(tot_b + tot_a) / tot_n * 100
        ci_p = (pm - 1.645 * pse, pm + 1.645 * pse)
        tost = "pass" if (ci_t[0] > -args.margin and ci_t[1] < args.margin) else "fail"
        out["metrics"][name] = {"per_seed_delta_pp": deltas, "mean_delta_pp": m, "ci90_seed_t": ci_t, "ci90_pooled": ci_p,
                                "mcnemar_p_per_seed": ps, "discordant_q_only": tot_b, "discordant_fp32_only": tot_a, "tost": tost}
        lines.append(f"| {name} | {', '.join(f'{d:+.2f}' for d in deltas)} | {m:+.2f} | [{ci_t[0]:+.2f}, {ci_t[1]:+.2f}] | [{ci_p[0]:+.2f}, {ci_p[1]:+.2f}] | "
                     f"{', '.join(f'{p:.2g}' for p in ps)} | {tost} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
