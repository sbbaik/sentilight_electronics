"""Seed-level and hierarchical statistics for paired model contrasts.

The row-level McNemar/Stouffer procedure treats 2,000 rows × 5 seeds as 10,000 paired observations,
which makes p-values tiny even when only 4 of 5 training replicates agree. The unit of replication
for a *training recipe* is the seed. This script therefore reports, for each contrast:

  1. per-seed paired differences (pp) on exact / coarse / strict, with min, max, SD
  2. seed-level mean difference with 90 % and 95 % t confidence intervals (df = n_seeds − 1)
  3. hierarchical bootstrap CI: resample seeds with replacement, then rows within each resampled
     seed with replacement (paired rows), B = 10,000
  4. random-effects (DerSimonian–Laird) pooled difference over seeds, using each seed's McNemar
     variance (b + c) / N² as the within-seed variance

Usage:
  python tools/seed_level_stats.py --seeds 42 43 44 45 46 \
     --contrast "W384->V2V4k=backend/reports/scale_grid_width/per_row/compactlm_W384_f100_s{s}.jsonl|backend/reports/scale_grid_vocab_natural/V4k/per_row/compactlm_V4k_f100_s{s}.jsonl" \
     --out backend/reports/scale_grid_combo/seed_level_stats
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIMS = ("H", "S", "B", "Dimmer", "CT")
T = {90: {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015}, 95: {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}}


def load(path: str, s: int) -> dict[int, tuple[int, int, int]]:
    out = {}
    for l in Path(path.format(s=s)).open(encoding="utf-8"):
        r = json.loads(l); p, ref = r.get("predicted"), r["reference"]
        out[r["row_index"]] = (int(bool(r["strict"])), int(bool(r["coarse"])), int(bool(p) and all(int(p[k]) == int(ref[k]) for k in DIMS)))
    return out


def paired(a: dict, b: dict, i: int) -> list[int]:
    ks = sorted(a.keys() & b.keys())
    return [b[k][i] - a[k][i] for k in ks]  # +1 if only b passes, −1 if only a passes, 0 otherwise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    ap.add_argument("--contrast", action="append", required=True, help="NAME=pathA|pathB with {s} for seed")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "backend/reports/scale_grid_combo/seed_level_stats")
    args = ap.parse_args()
    rng = random.Random(20260905)
    result = {}
    lines = ["# Seed-level and hierarchical statistics", "", f"- seeds {args.seeds}; hierarchical bootstrap B = {args.boot} (seeds, then paired rows within seed)", "",
             "| contrast | metric | per-seed Δ pp | mean | SD | min | max | 90 % CI (t) | 95 % CI (t) | 95 % CI (hier. bootstrap) | RE (DL) pooled Δ [95 %] | seeds > 0 |",
             "|---|---|---|--:|--:|--:|--:|---|---|---|---|--:|"]
    for spec in args.contrast:
        name, paths = spec.split("=", 1); pa, pb = paths.split("|")
        result[name] = {}
        diffs_by_seed = {s: [paired(load(pa, s), load(pb, s), i) for i in (2, 1, 0)] for s in args.seeds}  # exact, coarse, strict
        for mi, metric in enumerate(("exact", "coarse", "strict")):
            per = {s: 100 * st.mean(diffs_by_seed[s][mi]) for s in args.seeds}
            vals = list(per.values()); n = len(vals); m = st.mean(vals); sd = st.stdev(vals) if n > 1 else 0.0; se = sd / math.sqrt(n) if n > 1 else float("nan")
            ci90 = (m - T[90][n - 1] * se, m + T[90][n - 1] * se); ci95 = (m - T[95][n - 1] * se, m + T[95][n - 1] * se)
            # hierarchical bootstrap
            rows = {s: diffs_by_seed[s][mi] for s in args.seeds}
            import numpy as np
            nrng = np.random.default_rng(20260905 + mi)
            arrs = {s: np.asarray(rows[s], dtype=np.float64) for s in args.seeds}
            boots = np.empty(args.boot)
            seed_list = list(args.seeds)
            for bi in range(args.boot):
                tot = 0.0
                for s in nrng.choice(seed_list, size=n, replace=True):
                    r = arrs[s]; N = r.shape[0]
                    tot += 100 * r[nrng.integers(0, N, N)].mean()
                boots[bi] = tot / n
            boots.sort(); hb = (float(boots[int(0.025 * args.boot)]), float(boots[int(0.975 * args.boot) - 1]))
            # DerSimonian–Laird random effects over seeds
            ys, vs = [], []
            for s in args.seeds:
                r = rows[s]; N = len(r); b = sum(1 for x in r if x == 1); c = sum(1 for x in r if x == -1)
                ys.append(100 * (b - c) / N); vs.append(max(1e-9, 100 * 100 * (b + c) / N ** 2))
            w = [1 / v for v in vs]; yfe = sum(wi * yi for wi, yi in zip(w, ys)) / sum(w)
            Q = sum(wi * (yi - yfe) ** 2 for wi, yi in zip(w, ys)); C = sum(w) - sum(wi * wi for wi in w) / sum(w)
            tau2 = max(0.0, (Q - (n - 1)) / C) if C > 0 else 0.0
            wr = [1 / (v + tau2) for v in vs]; yre = sum(wi * yi for wi, yi in zip(wr, ys)) / sum(wr); sere = math.sqrt(1 / sum(wr))
            re_ci = (yre - 1.96 * sere, yre + 1.96 * sere)
            result[name][metric] = {"per_seed_pp": per, "mean": m, "sd": sd, "min": min(vals), "max": max(vals), "ci90_t": ci90, "ci95_t": ci95,
                                    "ci95_hier_bootstrap": hb, "re_dl": {"pooled": yre, "ci95": re_ci, "tau2": tau2}, "seeds_positive": sum(1 for v in vals if v > 0)}
            lines.append(f"| {name} | {metric} | {', '.join(f'{v:+.1f}' for v in vals)} | {m:+.2f} | {sd:.2f} | {min(vals):+.1f} | {max(vals):+.1f} | "
                         f"[{ci90[0]:+.2f}, {ci90[1]:+.2f}] | [{ci95[0]:+.2f}, {ci95[1]:+.2f}] | [{hb[0]:+.2f}, {hb[1]:+.2f}] | {yre:+.2f} [{re_ci[0]:+.2f}, {re_ci[1]:+.2f}] | {sum(1 for v in vals if v > 0)}/{n} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
