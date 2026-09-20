"""Cross-policy analysis of the K_eff series.

Reads the per-width analysis JSON of each K_eff column (K240 = the W series report root) and
produces one table: rows = K_eff, columns = d, cells = mean ± SD of a metric; plus a knee
estimate d* per column and the log-log slope of d* against K_eff.

Knee definition (pre-declared in config/width_series.json decision context):
  d*  = smallest d whose mean score reaches (max_score - tau * (max_score - min_score)),
        tau = 0.10  (i.e. within 10% of the column's own dynamic range of its best width)
  Also reported: d at which the largest adjacent gain occurs, and the first adjacent step that is
  NOT adopted (Holm p >= 0.05 or seed sign split) after an adopted rise.

Usage:
  python tools/analyze_keff_series.py --w-root backend/reports/scale_grid_width \
      --k-base backend/reports/scale_grid_keff_fs --out backend/reports/scale_grid_keff_fs/keff_analysis
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_column(root: Path) -> dict:
    p = root / "width_analysis.json"
    if not p.exists():
        raise SystemExit(f"missing {p}; run tools/analyze_width_series.py --report-root {root}")
    return json.loads(p.read_text(encoding="utf-8"))


def knee(table: list[dict], metric: str, tau: float) -> dict:
    xs = [t["d_model"] for t in table]
    ys = [t[f"{metric}_mean"] for t in table]
    lo, hi = min(ys), max(ys)
    thr = hi - tau * (hi - lo)
    d_star = next(x for x, y in zip(xs, ys) if y >= thr)
    gains = [(xs[i + 1], ys[i + 1] - ys[i]) for i in range(len(xs) - 1)]
    d_maxgain = max(gains, key=lambda g: g[1])[0] if gains else None
    return {"d_star": d_star, "threshold": thr, "max": hi, "min": lo, "d_of_largest_gain": d_maxgain,
            "curve": dict(zip(map(str, xs), ys))}


def first_flat_step(contrasts: list[dict], metric: str) -> str | None:
    seen_rise = False
    for c in contrasts:
        if c["metric"] != metric:
            continue
        if c["adopted"] and c["mean_delta_pp"] > 0:
            seen_rise = True
            continue
        if seen_rise:
            return c["step"]
    return None


def loglog_slope(pairs: list[tuple[float, float]]) -> dict:
    xs = [math.log(k) for k, _ in pairs]
    ys = [math.log(d) for _, d in pairs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return {"slope": float("nan"), "intercept": float("nan"), "r2": float("nan")}
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    icpt = my - slope * mx
    ss_res = sum((y - (icpt + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return {"slope": slope, "intercept": icpt, "r2": 1 - ss_res / ss_tot if ss_tot else float("nan"),
            "prediction_if_d_star_proportional_to_k_eff": 1.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--w-root", type=Path, default=REPO_ROOT / "backend/reports/scale_grid_width")
    ap.add_argument("--k-base", type=Path, default=REPO_ROOT / "backend/reports/scale_grid_keff_fs")
    ap.add_argument("--policies", nargs="*", default=["K48", "K480", "K960"])
    ap.add_argument("--tau", type=float, default=0.10)
    ap.add_argument("--levels", type=float, nargs="+", default=[50, 60, 70, 80])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    cols: dict[int, dict] = {240: load_column(args.w_root)}
    for p in args.policies:
        root = args.k_base / p
        if (root / "width_analysis.json").exists():
            cols[int(p[1:])] = load_column(root)
    keffs = sorted(cols)
    ds = sorted({t["d_model"] for c in cols.values() for t in c["table"]})
    common_ds = sorted(set.intersection(*[{t["d_model"] for t in c["table"]} for c in cols.values()]))

    lines = [f"# K_eff series analysis (tau = {args.tau})", "",
             f"- K240 column: `{args.w_root}` (W series); other columns: `{args.k_base}/<P>`",
             f"- Widths common to every column: {common_ds}", ""]
    result = {"tau": args.tau, "columns": {}, "knees": {}, "slopes": {}}
    for metric in ("exact", "coarse", "strict"):
        lines += [f"## {metric} (mean ± SD over seeds)", "",
                  "| K_eff | " + " | ".join(f"d={d}" for d in ds) + " | d* | largest gain at | first non-adopted step |",
                  "|--:|" + "--:|" * len(ds) + "--:|--:|---|"]
        pairs = []
        for k in keffs:
            c = cols[k]
            by_d = {t["d_model"]: t for t in c["table"]}
            kn = knee([t for t in c["table"] if t["d_model"] in common_ds] or c["table"], metric, args.tau)
            flat = first_flat_step(c["contrasts"], metric)
            cells = []
            for d in ds:
                t = by_d.get(d)
                cells.append(f"{t[f'{metric}_mean']:.1f} ± {t[f'{metric}_sd']:.1f}" if t else "·")
            lines.append(f"| {k} | " + " | ".join(cells) + f" | {kn['d_star']} | {kn['d_of_largest_gain']} | {flat or '-'} |")
            result["knees"].setdefault(metric, {})[k] = kn | {"first_non_adopted_step": flat}
            pairs.append((k, kn["d_star"]))
        sl = loglog_slope(pairs)
        result["slopes"][metric] = sl | {"pairs": pairs}
        lines += ["", f"log d* vs log K_eff: slope = {sl['slope']:.3f}, R² = {sl['r2']:.3f} "
                      f"(slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)", ""]
    # Absolute-level knees: smallest d whose mean EXACT score reaches a fixed level. Unlike the
    # relative tau knee these are comparable across columns whose ceilings differ.
    lines += ["## Absolute-level knee (exact tuple match): smallest d reaching the level", "",
              "| K_eff | " + " | ".join(f">= {lvl}%" for lvl in args.levels) + " |", "|--:|" + "--:|" * len(args.levels)]
    result["absolute_knees"] = {}
    for k in keffs:
        by_d = sorted((t["d_model"], t["exact_mean"]) for t in cols[k]["table"] if t["d_model"] in common_ds)
        row = {}
        for lvl in args.levels:
            hit = next((d for d, y in by_d if y >= lvl), None)
            row[str(lvl)] = hit
        result["absolute_knees"][k] = row
        lines.append(f"| {k} | " + " | ".join(str(row[str(l)]) if row[str(l)] else f"> {common_ds[-1]}" for l in args.levels) + " |")
    lines.append("")
    result["absolute_slopes"] = {}
    for lvl in args.levels:
        pairs = [(k, result["absolute_knees"][k][str(lvl)]) for k in keffs if result["absolute_knees"][k][str(lvl)]]
        if len(pairs) >= 2:
            sl = loglog_slope(pairs)
            result["absolute_slopes"][str(lvl)] = sl | {"pairs": pairs}
            lines.append(f"- level {lvl}%: pairs {pairs}; log d* vs log K_eff slope = {sl['slope']:.3f} (R² = {sl['r2']:.3f})")
    lines.append("")
    result["columns"] = {k: {"table": c["table"], "contrasts": c["contrasts"]} for k, c in cols.items()}
    out = args.out or (args.k_base / "keff_analysis")
    out.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
