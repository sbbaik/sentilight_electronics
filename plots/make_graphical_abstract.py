"""Graphical abstract for the IEEE Access submission: one wide panel row telling the paper's storyline.
Left: the executable policy collapses a nominal 1.3e11 actuator space to K_eff = 240 executable command tuples (a task
descriptor, not a width). Middle: the K series — smallest tested width passing 60 % exact vs K_eff under fixed steps, and the
attenuation under matched exposure (numbers from tables/T04). Right: the selected model vs the retrained deployed
architecture (tables/T10, T11). Output: GA_graphical_abstract.{png,pdf} (300 dpi) + data/GA_graphical_abstract.csv."""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
C = {"blue": "#2F6EBA", "orange": "#E07B39", "aqua": "#2BA3A6", "yellow": "#D9A400", "magenta": "#B4368F", "ink": "#1F2933", "ink2": "#52606D", "muted": "#9AA5B1", "surface": "#FFFFFF", "panel": "#F5F7FA"}
KE = "$K_{\\mathrm{eff}}$"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": C["muted"], "axes.labelcolor": C["ink"], "xtick.color": C["ink2"], "ytick.color": C["ink2"]})

# ---- numbers from the tables (five-seed cells where available)
K = [48, 240, 480, 960]; d60_fixed = [128, 192, 256, 384]                       # T04, fixed steps, smallest tested d >= 60 % exact
matched_384 = {"K48": 85.5, "K240": 81.9, "K480": 81.7, "K960": 80.7}          # S07: identical utterances (K48 test set), matched exposure, d = 384
fixed_384 = {"K48": 89.0, "K240": 81.9, "K480": 79.8, "K960": 70.5}            # S07: identical utterances (K48 test set), fixed steps, d = 384
sel = {"name": "selected\nd384 L8 V4k", "params": 15.7, "exact": 86.5, "sd": 1.8, "mb": 17.1, "ms": 95}   # T10, T11
dep = {"name": "deployed arch.\nd384 L8 V24k", "params": 23.4, "exact": 80.8, "sd": 3.6, "mb": 47.8, "ms": 101}

fig = plt.figure(figsize=(13.5, 5.2), dpi=100)
gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.25, 1.1], wspace=0.28, left=0.03, right=0.99, top=0.76, bottom=0.27)
fig.suptitle("If a task can issue only 240 actions, how large must the compact language model be?\nCount the executable actions, then search capacity and training exposure together", x=0.03, ha="left", fontsize=12.5, fontweight="bold", color=C["ink"], y=0.985, linespacing=1.3)
fig.text(0.03, 0.835, "SentiLight: Korean utterance → five-value bulb command, reproduced by a compact language model on an edge-assisted path", ha="left", fontsize=9.5, color=C["ink2"])

# ---- panel 1: from nominal space to K_eff
ax = fig.add_subplot(gs[0]); ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 10.5)
ax.text(0, 10.7, "1  What the task tells us", fontsize=10.5, fontweight="bold", color=C["ink"], va="top")
def box(ax, x, y, w, h, text, fc, ec, fs=9, tc=None, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.25", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc or C["ink"], fontweight="bold" if bold else "normal", linespacing=1.35)
box(ax, 0.3, 6.6, 9.4, 1.9, "Nominal actuator space\n|H|·|S|·|B|·|D|·|CT| ≈ 1.3 × 10¹¹ tuples", C["panel"], C["muted"], fs=9)
ax.add_patch(FancyArrowPatch((5, 6.5), (5, 5.3), arrowstyle="-|>", mutation_scale=16, color=C["ink2"], lw=1.4))
ax.text(5.25, 5.9, "executable policy π and device map f\n(7 colours, 5 emotions, 5 intensities)", fontsize=7.8, color=C["ink2"], va="center")
box(ax, 0.3, 3.3, 9.4, 1.9, "Effective action set  $\\mathcal{A}_{\\mathrm{eff}}$ = {f(a) : a ∈ $\\mathcal{A}_{\\mathrm{valid}}$(π)}\n" + KE + " = |$\\mathcal{A}_{\\mathrm{eff}}$| = (7+1)(5+1)×5 = 240,  0 collisions", "#E8F0FA", C["blue"], fs=9.2, bold=True)
ax.text(0.3, 2.7, KE + " is a task descriptor: not a hidden width, not a term in\nN ≈ V·d + 12·L·d².  It reaches model size only through the\naccuracy constraint of a search over (d, L, V, budget).", fontsize=8.2, color=C["ink"], va="top", linespacing=1.4)

# ---- panel 2: K series evidence
ax = fig.add_subplot(gs[1])
ax.set_title("2  Evidence from four nested policies (" + KE + " 48–960)", loc="left", fontsize=10.5, fontweight="bold", color=C["ink"], pad=8)
ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
ax.plot(K, d60_fixed, color=C["blue"], lw=2.2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2, label="fixed step budget: smallest tested d ≥ 60 % exact")
for k, d in zip(K, d60_fixed): ax.annotate(f"d = {d}", (k, d), textcoords="offset points", xytext=(-4, 9) if k == 48 else (6, -12), ha="left" if k != 48 else "left", fontsize=7.8, color=C["ink2"])
ax.set_xticks(K); ax.set_xticklabels([str(k) for k in K]); ax.set_yticks([128, 192, 256, 384]); ax.set_yticklabels(["128", "192", "256", "384"])
ax.set_xlabel(KE + " (executable actions)"); ax.set_ylabel("threshold-passing width d")
ax.set_ylim(60, 560); ax.grid(True, color="#E4E7EB", lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(loc="upper left", fontsize=7.6, frameon=False)
txt = ("K48 test set (identical utterances), d = 384, exact %\n"
       f"fixed steps:  K48 {fixed_384['K48']:.1f} · K240 {fixed_384['K240']:.1f}\n"
       f"    · K480 {fixed_384['K480']:.1f} · K960 {fixed_384['K960']:.1f}\n"
       f"matched exposure:  K48 {matched_384['K48']:.1f} · K240 {matched_384['K240']:.1f}\n"
       f"    · K480 {matched_384['K480']:.1f} · K960 {matched_384['K960']:.1f}\n"
       "→ loss extends to shared actions; matching\n   exposure attenuates mean gaps (CIs inconclusive)")
ax.text(0.98, 0.03, txt, transform=ax.transAxes, fontsize=7.1, color=C["ink"], va="bottom", ha="right", linespacing=1.4, bbox=dict(boxstyle="round,pad=0.4", fc=C["panel"], ec=C["muted"], lw=0.8))

# ---- panel 3: outcome
ax = fig.add_subplot(gs[2])
ax.set_title("3  Outcome: a smaller, steadier deployable model", loc="left", fontsize=10.5, fontweight="bold", color=C["ink"], pad=8)
names = [dep["name"], sel["name"]]; vals = [dep["exact"], sel["exact"]]; errs = [dep["sd"], sel["sd"]]; cols = [C["muted"], C["blue"]]
bars = ax.bar([0, 1], vals, width=0.58, color=cols, edgecolor=C["surface"], linewidth=1.5, yerr=errs, capsize=4, error_kw=dict(ecolor=C["ink2"], lw=1.2))
ax.set_xticks([0, 1]); ax.set_xticklabels(names, fontsize=8.6); ax.set_ylim(60, 95); ax.set_ylabel("exact tuple match (%)  mean ± SD, 5 seeds")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(True, axis="y", color="#E4E7EB", lw=0.8); ax.set_axisbelow(True)
ax.text(0, dep["exact"] + dep["sd"] + 1.0, f"{dep['exact']:.1f} ± {dep['sd']:.1f}\n{dep['params']} M params", ha="center", va="bottom", fontsize=8.2, color=C["ink"])
ax.text(1, sel["exact"] + sel["sd"] + 1.0, f"{sel['exact']:.1f} ± {sel['sd']:.1f}\n{sel['params']} M params", ha="center", va="bottom", fontsize=8.2, color=C["ink"])
ax.text(0.5, -0.22, f"+5.8 pp (90 % CI [+1.1, +10.5]); −33 % parameters\nmixed 4/6/8-bit: {sel['mb']} MB, equivalent within ±3 pp\nshared CPU (4 threads): {sel['ms']} ms median\nselected on mean, seed variance and downside; depth by\nmulti-seed screening (not derivable from the policy)",
        transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color=C["ink"], linespacing=1.4, bbox=dict(boxstyle="round,pad=0.4", fc=C["panel"], ec=C["muted"], lw=0.8))

fig.savefig(HERE / "GA_graphical_abstract.png", dpi=300, bbox_inches="tight"); fig.savefig(HERE / "GA_graphical_abstract.pdf", bbox_inches="tight")
with (HERE / "data" / "GA_graphical_abstract.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["panel", "item", "value", "source"])
    for k, d in zip(K, d60_fixed): w.writerow(["2", f"d60_fixed_steps_K{k}", d, "tables/T04"])
    for k, v in fixed_384.items(): w.writerow(["2", f"K48test_fixed_steps_d384_{k}_exact", v, "tables/S07"])
    for k, v in matched_384.items(): w.writerow(["2", f"K48test_matched_exposure_d384_{k}_exact", v, "tables/S07"])
    for lab, m in (("deployed_arch", dep), ("selected", sel)):
        for key in ("params", "exact", "sd", "mb", "ms"): w.writerow(["3", f"{lab}_{key}", m[key], "tables/T10,T11"])
print("written GA_graphical_abstract.png/pdf")
