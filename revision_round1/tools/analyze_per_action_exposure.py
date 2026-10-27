# -*- coding: utf-8 -*-
"""Per-action training exposure against per-action exact match (Reviewer 3, point 2).

The paper reports a mean of ~205 training rows per action and a minimum of 18. This script puts every one of
the 240 cells on the page: how many training rows it had, and how often the selected model reproduced it on
the development test and on the unseen-frame hold-out, averaged over five seeds. The least-exposed cells are
reported separately with a seed interval, which is what the reviewer asked for.

Inputs are the released artefacts only: the K240 training rows, and the per-row evaluation outputs.
"""
from __future__ import annotations

import collections
import json
import math
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parents[1]
TRAIN = HERE / "data/datasets/K240_keff/train_100.jsonl"
DEV = HERE / "data/per_row/dev_V4k"
UNSEEN = HERE / "data/per_row/unseen_frames"
OUT = HERE / "analysis/per_action_exposure"
DIMS = ("H", "S", "B", "Dimmer", "CT")
LOW_N = 5                         # the least-exposed cells reported individually


def cell_of(r):
    return (r.get("base_color") or "none", r.get("emotion") or "none", r.get("intensity") or "neutral")


def key(o):
    return tuple(int(o[d]) for d in DIMS) if o else None


def per_cell_accuracy(per_row_dir: Path, pattern: str):
    """{seed: {cell: [correct flags]}} from one family's per-row files."""
    out = {}
    for f in sorted(per_row_dir.glob(pattern)):
        seed = int(f.stem.rsplit("s", 1)[1])
        acc = collections.defaultdict(list)
        for line in f.open(encoding="utf-8"):
            r = json.loads(line)
            acc[cell_of(r)].append(key(r.get("predicted")) == key(r["reference"]))
        out[seed] = acc
    return out


def t90(xs):
    """Mean and 90 % t interval across seeds (n−1 df)."""
    n = len(xs); m = st.mean(xs)
    if n < 2:
        return m, float("nan"), float("nan")
    sd = st.stdev(xs); tcrit = {2: 6.314, 3: 2.920, 4: 2.353, 5: 2.132}[n]
    h = tcrit * sd / math.sqrt(n)
    return m, m - h, m + h


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    exposure = collections.Counter(cell_of(json.loads(l)) for l in TRAIN.open(encoding="utf-8"))
    assert len(exposure) == 240, len(exposure)

    sets = {"development": per_cell_accuracy(DEV, "compactlm_V4k_f100_s*.jsonl"),
            "unseen_frames": per_cell_accuracy(UNSEEN, "selected_V4k_L8_s4*.jsonl")}
    for name, by_seed in sets.items():
        assert len(by_seed) == 5, (name, list(by_seed))

    cells = sorted(exposure, key=exposure.get)
    rows = []
    for c in cells:
        rec = {"cell": {"colour": c[0], "emotion": c[1], "intensity": c[2]}, "train_rows": exposure[c]}
        for name, by_seed in sets.items():
            per_seed = [100 * st.mean(by_seed[s][c]) for s in sorted(by_seed) if by_seed[s].get(c)]
            n_rows = [len(by_seed[s].get(c, [])) for s in sorted(by_seed)]
            m, lo, hi = t90(per_seed) if per_seed else (float("nan"),) * 3
            rec[name] = {"exact_mean": round(m, 1), "ci90": [round(lo, 1), round(hi, 1)],
                         "per_seed": [round(x, 1) for x in per_seed], "eval_rows_per_seed": n_rows[0] if n_rows else 0}
        rows.append(rec)

    # association between exposure and accuracy, descriptive only
    x = np.array([r["train_rows"] for r in rows], dtype=float)
    summary = {"n_cells": 240, "train_rows": {"min": int(x.min()), "median": float(np.median(x)),
                                              "mean": round(float(x.mean()), 1), "max": int(x.max())}}
    for name in sets:
        y = np.array([r[name]["exact_mean"] for r in rows])
        ok = ~np.isnan(y)
        rho = float(np.corrcoef(np.argsort(np.argsort(x[ok])), np.argsort(np.argsort(y[ok])))[0, 1])
        # quartiles of exposure
        qs = np.quantile(x, [0.25, 0.5, 0.75])
        bands = {}
        for lab, lo_, hi_ in (("Q1 (lowest)", -1, qs[0]), ("Q2", qs[0], qs[1]), ("Q3", qs[1], qs[2]), ("Q4 (highest)", qs[2], 1e9)):
            m = (x > lo_) & (x <= hi_) & ok
            bands[lab] = {"cells": int(m.sum()), "exposure_range": [int(x[m].min()), int(x[m].max())],
                          "exact_mean_of_cells": round(float(y[m].mean()), 1)}
        summary[name] = {"spearman_rho_exposure_vs_exact": round(rho, 3), "exposure_quartiles": bands,
                         "least_exposed": [{**rows[i]["cell"], "train_rows": rows[i]["train_rows"],
                                            **rows[i][name]} for i in range(LOW_N)]}

    (OUT / "per_action_exposure.json").write_text(json.dumps({"summary": summary, "cells": rows}, indent=1,
                                                              ensure_ascii=False), encoding="utf-8")

    # -------- figure: exposure vs exact match, both sets, least-exposed cells marked
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=200, sharey=True)
    for ax, name, title in zip(axes, sets, ("Development test", "Unseen-frame hold-out")):
        y = np.array([r[name]["exact_mean"] for r in rows]); lo = np.array([r[name]["ci90"][0] for r in rows]); hi = np.array([r[name]["ci90"][1] for r in rows])
        ax.errorbar(x, y, yerr=[np.clip(y - lo, 0, None), np.clip(hi - y, 0, None)], fmt="o", ms=3.2, lw=0.6,
                    color="#2f6db3", ecolor="#9db8d8", alpha=0.85, label="policy cell (5-seed mean, 90 % t interval)")
        ax.scatter(x[:LOW_N], y[:LOW_N], s=70, facecolors="none", edgecolors="#c0392b", linewidths=1.6,
                   label=f"{LOW_N} least-exposed cells", zorder=5)
        ax.set_xscale("log"); ax.set_xlabel("training rows for the cell (log scale)")
        ax.set_ylim(-2, 102); ax.set_xticks([20, 50, 100, 200, 300]); ax.set_xticklabels(["20", "50", "100", "200", "300"])
        ax.set_title(title, fontsize=10); ax.grid(alpha=0.25, which="both")
        ax.text(0.02, 0.04, f"Spearman ρ = {summary[name]['spearman_rho_exposure_vs_exact']:+.2f}",
                transform=ax.transAxes, fontsize=8.5, color="#333")
    axes[0].set_ylabel("exact tuple match (%)"); axes[0].legend(fontsize=7.5, loc="lower right")
    for ax in axes:
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.patch.set_facecolor("white"); fig.tight_layout()
    fig.savefig(OUT / "per_action_exposure.png", facecolor="white"); plt.close(fig)

    # -------- markdown summary
    md = ["# Per-action training exposure and policy reproduction", "",
          f"240 cells; training rows per cell min {summary['train_rows']['min']}, median {summary['train_rows']['median']:.0f}, "
          f"mean {summary['train_rows']['mean']}, max {summary['train_rows']['max']}.", ""]
    for name in sets:
        s_ = summary[name]
        md += [f"## {name}", "", f"Spearman ρ (exposure vs exact) = {s_['spearman_rho_exposure_vs_exact']:+.3f}", "",
               "| exposure quartile | cells | rows/cell | mean exact % |", "|---|--:|---|--:|"]
        md += [f"| {k} | {v['cells']} | {v['exposure_range'][0]}–{v['exposure_range'][1]} | {v['exact_mean_of_cells']} |" for k, v in s_["exposure_quartiles"].items()]
        md += ["", f"### {LOW_N} least-exposed cells", "", "| colour | emotion | intensity | train rows | exact % (5 seeds) | 90 % interval |", "|---|---|---|--:|--:|---|"]
        md += [f"| {c['colour']} | {c['emotion']} | {c['intensity']} | {c['train_rows']} | {c['exact_mean']} | [{c['ci90'][0]}, {c['ci90'][1]}] |" for c in s_["least_exposed"]]
        md.append("")
    (OUT / "per_action_exposure.md").write_text("\n".join(md), encoding="utf-8")

    for name in sets:
        s_ = summary[name]
        print(f"  {name}: rho={s_['spearman_rho_exposure_vs_exact']:+.3f}  quartile means "
              + " / ".join(f"{v['exact_mean_of_cells']}" for v in s_["exposure_quartiles"].values()))
        for c in s_["least_exposed"]:
            print(f"     {c['train_rows']:>3} rows  {c['colour']:>7}/{c['emotion']:>9}/{c['intensity']:<7}  {c['exact_mean']:5.1f}  [{c['ci90'][0]}, {c['ci90'][1]}]")
    print("  written", OUT)


if __name__ == "__main__":
    main()
