"""Aggregate a width-series (or one K_eff column) and test adjacent-width steps.

Per width (mean ± SD over seeds): strict, coarse, exact-tuple match, parameters, latency.
Adjacent widths: per-seed exact McNemar on paired test rows -> signed z -> Stouffer -> Holm over
(6 steps x 3 metrics). Adopt only if Holm p < 0.05 and all seeds share the sign.

Usage:
  python tools/analyze_width_series.py --report-root backend/reports/scale_grid_width
  python tools/analyze_width_series.py --report-root backend/reports/scale_grid_keff/K960
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics as st
from collections import defaultdict
from math import comb
from pathlib import Path
from statistics import NormalDist

SORT_KEY = "n_layer" if "--by-layer" in __import__("sys").argv else "d_model"
RUN_RE = re.compile(r"^compactlm_(?P<scale>[^_]+)_f(?P<fraction>\d+)_s(?P<seed>\d+)$")
DIMS = ("H", "S", "B", "Dimmer", "CT")
N = NormalDist()


def load_per_row(path: Path) -> dict[int, tuple[bool, bool, bool]]:
    out = {}
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        pred, ref = r.get("predicted"), r.get("reference")
        exact = bool(pred) and all(int(pred[k]) == int(ref[k]) for k in DIMS)
        out[r["row_index"]] = (bool(r.get("strict")), bool(r.get("coarse")), exact)
    return out


def mcnemar(a: dict, b: dict, idx: int) -> tuple[int, int, float]:
    keys = a.keys() & b.keys()
    bo = sum(1 for k in keys if b[k][idx] and not a[k][idx])
    ao = sum(1 for k in keys if a[k][idx] and not b[k][idx])
    n, k = bo + ao, min(bo, ao)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return bo, ao, max(p, 1e-15)


def holm(pvals: list[float]) -> list[float]:
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj = [0.0] * len(pvals)
    running = 0.0
    m = len(pvals)
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-root", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--by-layer", action="store_true")
    args = ap.parse_args()
    root = args.report_root
    runs: dict[str, dict[int, dict]] = defaultdict(dict)
    for p in sorted((root / "run_summaries").glob("*.json")):
        m = RUN_RE.match(p.stem)
        if not m:
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        per_row_path = root / "per_row" / f"{p.stem}.jsonl"
        rows = load_per_row(per_row_path) if per_row_path.exists() else {}
        j["_rows"] = rows
        j["_exact"] = (sum(1 for v in rows.values() if v[2]) / len(rows)) if rows else float("nan")
        runs[m.group("scale")][int(m.group("seed"))] = j
    d_of = {s: next(iter(v.values()))["model_config"][SORT_KEY] for s, v in runs.items()}
    scales = sorted(runs, key=lambda s: d_of[s])

    table = []
    for s in scales:
        seeds = sorted(runs[s])
        strict = [runs[s][x]["metrics"]["strict_semantic_pass_rate"] * 100 for x in seeds]
        coarse = [runs[s][x]["metrics"]["coarse_3bin_pass_rate"] * 100 for x in seeds]
        exact = [runs[s][x]["_exact"] * 100 for x in seeds]
        lat = [runs[s][x]["metrics"]["latency"]["mean_ms"] for x in seeds]
        sd = lambda v: st.stdev(v) if len(v) > 1 else 0.0
        table.append({"scale": s, "d_model": d_of[s], "params": runs[s][seeds[0]]["parameter_count"], "seeds": seeds,
                      "strict_mean": st.mean(strict), "strict_sd": sd(strict), "coarse_mean": st.mean(coarse), "coarse_sd": sd(coarse),
                      "exact_mean": st.mean(exact), "exact_sd": sd(exact), "latency_ms": st.mean(lat),
                      "per_seed": {str(x): {"strict": strict[i], "coarse": coarse[i], "exact": exact[i]} for i, x in enumerate(seeds)}})

    contrasts = []
    for a, b in zip(scales, scales[1:]):
        for mname, idx in (("strict", 0), ("coarse", 1), ("exact", 2)):
            zs, deltas, per_seed = [], [], {}
            for seed in sorted(set(runs[a]) & set(runs[b])):
                ra, rb = runs[a][seed]["_rows"], runs[b][seed]["_rows"]
                if not ra or not rb:
                    continue
                bo, ao, p = mcnemar(ra, rb, idx)
                delta = (bo - ao) / len(ra.keys() & rb.keys()) * 100
                z = -N.inv_cdf(p / 2) * (1 if delta > 0 else -1 if delta < 0 else 0)
                zs.append(z); deltas.append(delta)
                per_seed[str(seed)] = {"big_only": bo, "small_only": ao, "delta_pp": delta, "p": p}
            if not zs:
                continue
            Z = sum(zs) / math.sqrt(len(zs))
            pc = 2 * (1 - N.cdf(abs(Z)))
            signs_ok = all(x > 0 for x in deltas) or all(x < 0 for x in deltas)
            contrasts.append({"step": f"{a}->{b}", "metric": mname, "mean_delta_pp": st.mean(deltas), "stouffer_z": Z, "p": pc,
                              "seed_signs_consistent": signs_ok, "per_seed": per_seed})
    adj = holm([c["p"] for c in contrasts]) if contrasts else []
    for c, pa in zip(contrasts, adj):
        c["holm_p"] = pa
        c["adopted"] = pa < 0.05 and c["seed_signs_consistent"]

    lines = [f"# Width-series analysis: `{root}`", "",
             "| Scale | " + ("L" if SORT_KEY == "n_layer" else "d") + " | Params | Strict % | Coarse % | Exact tuple % | Latency ms |", "|---|--:|--:|--:|--:|--:|--:|"]
    for t in table:
        lines.append(f"| {t['scale']} | {t['d_model']} | {t['params']:,} | {t['strict_mean']:.2f} ± {t['strict_sd']:.2f} | "
                     f"{t['coarse_mean']:.2f} ± {t['coarse_sd']:.2f} | {t['exact_mean']:.2f} ± {t['exact_sd']:.2f} | {t['latency_ms']:.0f} |")
    lines += ["", "## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)", "",
              "| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |", "|---|---|--:|--:|--:|---|---|"]
    for c in contrasts:
        lines.append(f"| {c['step']} | {c['metric']} | {c['mean_delta_pp']:+.2f} | {c['stouffer_z']:+.2f} | {c['holm_p']:.2e} | "
                     f"{'yes' if c['seed_signs_consistent'] else 'NO'} | {'adopted' if c['adopted'] else '-'} |")
    md = "\n".join(lines) + "\n"
    out_json = args.out_json or root / "width_analysis.json"
    out_md = args.out_md or root / "width_analysis.md"
    out_json.write_text(json.dumps({"table": table, "contrasts": contrasts}, ensure_ascii=False, indent=1), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
