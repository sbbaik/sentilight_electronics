# -*- coding: utf-8 -*-
"""The common-K48 test as a main-text figure (Reviewer 1 point 1, Reviewer 2 point 1).

Every policy model is scored on the same 2,000 K48 utterances whose gold tuple is identical under all four
policies, so differences cannot come from different test sets or from the added actions. This is the paper's
strongest evidence that growing the action set costs accuracy on actions the policies share; in v50 it sits in
Supplementary S7. Numbers come from that table unchanged.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
S07 = HERE / "data/tables/S07_keff_common_test_set.csv"
OUT = HERE / "figures"
KEFF = {"K48": 48, "K240": 240, "K480": 480, "K960": 960}


def pm(s):
    m = re.match(r"\s*([\d.]+)\s*±\s*([\d.]+)", s)
    return float(m.group(1)), float(m.group(2))


def main():
    OUT.mkdir(exist_ok=True)
    pts = {}
    for r in csv.DictReader(S07.open(encoding="utf-8")):
        if r["policy / contrast"] in KEFF and r["exact % on K48 test"]:
            acc, sd = pm(r["exact % on K48 test"])
            pts.setdefault((r["SFT budget"], int(r["d"])), []).append(
                {"policy": r["policy / contrast"], "keff": KEFF[r["policy / contrast"]], "exact": acc, "sd": sd, "seeds": int(r["seeds"])})
    RS = json.loads((HERE / "analysis/random_subsets/random_subsets.json").read_text(encoding="utf-8"))["grid"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.6), dpi=200, sharey="row")
    colours = {256: "#e07b39", 384: "#2f6db3"}
    for ax, budget, title in zip(axes[0], ("fixed steps", "fixed epochs"),
                                 ("(a) Nested policies, fixed step budget", "(b) Nested policies, matched presentations per action")):
        for d in (256, 384):
            series = sorted(pts[(budget, d)], key=lambda p: p["keff"])
            x = [p["keff"] for p in series]; y = [p["exact"] for p in series]; e = [p["sd"] for p in series]
            ax.errorbar(x, y, yerr=e, fmt="o-", color=colours[d], ecolor=colours[d], ms=4.5, lw=1.2, capsize=2.5, alpha=0.9, label=f"d = {d}")
            for p in series:
                if p["seeds"] < 5:
                    ax.scatter([p["keff"]], [p["exact"]], s=60, facecolors="white", edgecolors=colours[d], zorder=5)
        ax.set_xscale("log", base=2); ax.set_xticks([48, 240, 480, 960]); ax.set_xticklabels(["48", "240", "480", "960"])
        ax.set_xlabel("K_eff of the nested training policy (categories added with K_eff)"); ax.set_title(title, fontsize=9.5); ax.grid(alpha=0.25, which="both")
    axes[0][0].set_ylabel("exact match on the common K48 test (%)")
    axes[0][0].legend(fontsize=8, loc="lower left", title="hidden size", title_fontsize=8)
    axes[0][1].text(0.98, 0.04, "hollow marker = 3 seeds; filled = 5 seeds\nerror bars = sample SD across seeds", transform=axes[0][1].transAxes, fontsize=7.5, ha="right", color="#444")
    for ax, sched, title in zip(axes[1], ("fixed", "matched"),
                                ("(c) Random subsets of K240, fixed step budget", "(d) Random subsets of K240, matched presentations per action")):
        for d in (256, 384):
            cells = [(k, RS[f"{sched}|d{d}|common|{pol}"]) for pol, k in (("K48r", 48), ("K96r", 96), ("K144r", 144), ("K240", 240)) if f"{sched}|d{d}|common|{pol}" in RS]
            ax.errorbar([c[0] for c in cells], [c[1]["mean"] for c in cells], yerr=[c[1]["sd"] for c in cells], fmt="o-", color=colours[d], ecolor=colours[d], ms=4.5, lw=1.2, capsize=2.5, alpha=0.9, label=f"d = {d}")
            for c in cells:
                if c[1]["seeds"] < 5:
                    ax.scatter([c[0]], [c[1]["mean"]], s=60, facecolors="white", edgecolors=colours[d], zorder=5)
        ax.set_xscale("log", base=2); ax.set_xticks([48, 96, 144, 240]); ax.set_xticklabels(["48", "96", "144", "240"])
        ax.set_xlabel("cells in the training policy (same categories, K240 exposure per cell)"); ax.set_title(title, fontsize=9.5); ax.grid(alpha=0.25, which="both")
    axes[1][0].set_ylabel("exact match on the common K48r test (%)")
    axes[1][1].text(0.98, 0.04, "hollow marker = 3 seeds; filled = 5 seeds\nerror bars = sample SD across seeds", transform=axes[1][1].transAxes, fontsize=7.5, ha="right", color="#444")
    for row in axes:
        for ax in row:
            for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.suptitle("Accuracy on shared actions as the action set grows: nested policies (top) and random subsets with composition fixed (bottom)", fontsize=9.5, y=0.995)
    fig.patch.set_facecolor("white"); fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "F_common_k48.png", facecolor="white"); plt.close(fig)
    (OUT / "F_common_k48.json").write_text(json.dumps({f"{b}|d{d}": v for (b, d), v in pts.items()}, indent=1), encoding="utf-8")
    for (b, d), v in sorted(pts.items()):
        print(f"  {b:12s} d={d}: " + "  ".join(f"K{p['keff']}={p['exact']}±{p['sd']}({p['seeds']}s)" for p in sorted(v, key=lambda p: p['keff'])))
    print("  written", OUT / "F_common_k48.png")


if __name__ == "__main__":
    main()
