# -*- coding: utf-8 -*-
"""Redraw the data figures of v51 in one style at print size (all three reviewers: "figures can be improved").

Every number comes from a stored result file; nothing is recomputed:
  Fig 3, 6, 8, 11  the v1.0.0 package analysis/ files (and plots/data CSVs for Figs 10, 11)
  Fig 4, 5, 7, 9   the revision analysis outputs (analysis/*.json, figures/F_common_k48.json)
Figures are drawn at the width they occupy on the page (6.3 in), so 8 pt type prints at 8 pt. Each figure is written
as PNG (600 dpi) and PDF to figures/v51/.

Shared encoding across figures: orange = selected model / 4k natural tokenizer, blue = production 24k tokenizer /
deployed architecture, aqua = other natural tokenizers, the A = 2 control and the 240-class head, grey = negative
control; filled markers = five seeds, hollow = three seeds; error bars = sample SD across seeds.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
PKG = HERE.parent if (HERE.parent / "analysis").is_dir() else HERE.parent / "MDPI_Electronics_submitted_1st" / "sentilight_electronics"   # in the release: the v1.0.0 package root
A = PKG / "analysis"
OUT = HERE / "figures" / "v51"
sys.path.insert(0, str(HERE / "tools"))
from analyze_audited_requests import PAPER, PAPER_SD, SOURCES  # noqa: E402

C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "grey": "#8a8985", "red": "#c0392b",
     "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e6e5e1", "pale": "#a9c7ec"}
SEQ = {"48": "#86b6ef", "240": "#5598e7", "480": "#256abf", "960": "#104281"}
W = 6.3
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7, "legend.frameon": False,
                     "axes.edgecolor": C["ink2"], "axes.linewidth": 0.7, "axes.spines.top": False, "axes.spines.right": False,
                     "xtick.color": C["ink2"], "ytick.color": C["ink2"], "text.color": C["ink"], "axes.labelcolor": C["ink"],
                     "axes.titlelocation": "left", "axes.titlepad": 5, "grid.color": C["grid"], "grid.linewidth": 0.6,
                     "lines.linewidth": 1.5, "errorbar.capsize": 2, "figure.dpi": 100, "savefig.dpi": 600,
                     "pdf.fonttype": 42, "figure.facecolor": "white", "axes.facecolor": "white"})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.03)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig); print("  written", name)


def ygrid(ax, axis="y"):
    ax.grid(axis=axis, zorder=0); ax.set_axisbelow(True)


def mark(ax, x, y, col, five, s=22, z=4):
    ax.scatter(x, y, s=s, facecolors=col if five else "white", edgecolors=col, linewidths=1.1, zorder=z)


def seed_key(ax, loc="lower right", col=None, extra=()):
    col = col or C["ink2"]
    h = list(extra) + [Line2D([], [], marker="o", lw=0, ms=4.5, color=col, label="five seeds"),
                       Line2D([], [], marker="o", lw=0, ms=4.5, color=col, markerfacecolor="white", label="three seeds")]
    ax.legend(handles=h, loc=loc)


def table(root):
    return json.loads((A / root / "width_analysis.json").read_text(encoding="utf-8"))["table"]


def per_seed_dots(ax, x, r, col):
    v = [p["exact"] for p in r["per_seed"].values()]
    ax.scatter([x] * len(v), v, s=7, color=col, alpha=0.35, lw=0, zorder=3)


# ---------------------------------------------------------------- Fig 3: K_eff series
def fig3():
    fs = json.loads((A / "scale_grid_keff_fs/keff_analysis.json").read_text(encoding="utf-8"))
    fe = json.loads((A / "scale_grid_keff/keff_analysis_fixed_epochs.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.35), gridspec_kw={"width_ratios": [1, 1, 0.82], "wspace": 0.42})
    for ax, res, title in ((axes[0], fs, "(a) Fixed step budget"), (axes[1], fe, "(b) Matched presentations")):
        for k in ("48", "240", "480", "960"):
            tb = sorted((r for r in res["columns"][k]["table"] if r["d_model"] in (128, 192, 256, 384, 512)), key=lambda r: r["d_model"])
            xs = [r["d_model"] for r in tb]; ys = [r["exact_mean"] for r in tb]
            ax.plot(xs, ys, color=SEQ[k], zorder=3, label=k)
            for x, y, r in zip(xs, ys, tb): mark(ax, x, y, SEQ[k], len(r["seeds"]) >= 5, s=16)
        ax.axhline(60, color=C["grey"], lw=0.8, ls=(0, (3, 2)), zorder=1)
        ax.set_xscale("log", base=2); ax.set_xticks([128, 192, 256, 384, 512]); ax.set_xticklabels(["128", "192", "256", "384", "512"]); ax.minorticks_off()
        ax.set_xlim(115, 570); ax.set_ylim(0, 100)
        ax.set_xlabel("hidden size d (L = 8)"); ax.set_title(title); ygrid(ax)
    axes[0].set_ylabel("exact tuple match (%)")
    axes[0].text(560, 61.5, "60% line", ha="right", va="bottom", fontsize=6.5, color=C["ink2"])
    axes[1].legend(title="K_eff", loc="lower right", title_fontsize=7, handlelength=1.4)
    ax = axes[2]; ks = [48, 240, 480, 960]; ds = [fs["absolute_knees"][str(k)]["60"] for k in ks]
    ax.plot(ks, ds, color=C["blue"], marker="o", ms=4.5, markeredgecolor="white", zorder=3)
    ax.set_xscale("log", base=2); ax.set_yscale("log", base=2)
    ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.minorticks_off()
    ax.set_yticks([128, 192, 256, 384, 512]); ax.set_yticklabels(["128", "192", "256", "384", "512"])
    ax.set_xlabel("K_eff"); ax.set_ylabel("smallest d at or above 60%")
    ax.set_title(f"(c) Knee, slope {fs['absolute_slopes']['60']['slope']:.2f}"); ygrid(ax)
    fig.legend(handles=[Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], label="five seeds"),
                        Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], markerfacecolor="white", label="three seeds")],
               loc="upper right", ncol=2, bbox_to_anchor=(1.0, 1.08))
    save(fig, "Figure03_keff_series")


# ---------------------------------------------------------------- Fig 4: shared-action accuracy
def fig4():
    pts = json.loads((HERE / "figures/F_common_k48.json").read_text(encoding="utf-8"))
    RSJ = json.loads((HERE / "analysis/random_subsets/random_subsets.json").read_text(encoding="utf-8"))
    RS, DR = RSJ["grid"], RSJ["draws"]["per_draw"]
    col = {256: C["aqua"], 384: C["blue"]}
    fig, axes = plt.subplots(2, 2, figsize=(W, 4.7), sharey="row", gridspec_kw={"hspace": 0.62, "wspace": 0.08})
    for ax, budget, title in zip(axes[0], ("fixed steps", "fixed epochs"), ("(a) Nested policies, fixed steps", "(b) Nested policies, matched presentations")):
        for d in (256, 384):
            s = sorted(pts[f"{budget}|d{d}"], key=lambda p: p["keff"])
            x = [p["keff"] for p in s]; y = [p["exact"] for p in s]
            ax.errorbar(x, y, yerr=[p["sd"] for p in s], color=col[d], ecolor=col[d], elinewidth=0.9, zorder=3)
            for p in s: mark(ax, p["keff"], p["exact"], col[d], p["seeds"] >= 5, z=5)
        ax.set_xscale("log", base=2); ax.set_xticks([48, 240, 480, 960]); ax.set_xticklabels(["48", "240", "480", "960"]); ax.minorticks_off()
        ax.set_xlim(40, 1150); ax.set_xlabel("K_eff of the nested training policy"); ax.set_title(title); ygrid(ax)
    axes[0][0].set_ylabel("exact match, common K48 test (%)")
    for ax, sched, title in zip(axes[1], ("fixed", "matched"), ("(c) Random subsets of K240, fixed steps", "(d) Random subsets of K240, matched")):
        for d in (256, 384):
            cells = [(k, RS[f"{sched}|d{d}|common|{p}"]) for p, k in (("K48r", 48), ("K96r", 96), ("K144r", 144), ("K240", 240))]
            ax.errorbar([c[0] for c in cells], [c[1]["mean"] for c in cells], yerr=[c[1]["sd"] for c in cells], color=col[d], ecolor=col[d], elinewidth=0.9, zorder=3)
            for k, c in cells: mark(ax, k, c["mean"], col[d], c["seeds"] >= 5, z=5)
        # two further independent draws at d = 384, each on its own common test (their SDs are in Table S34)
        for n, ls in (("2", (0, (4, 2))), ("3", (0, (1.2, 1.6)))):
            g = DR[sched][n]["grid"]
            xs, ys = [48, 96, 144, 240], [g[p]["mean"] for p in ("K48r", "K96r", "K144r", "K240")]
            ax.plot(xs, ys, color=C["blue"], lw=1.0, ls=ls, alpha=0.85, zorder=2)
            ax.scatter(xs, ys, s=9, color=C["blue"], alpha=0.85, lw=0, zorder=2)
            up = n == "2" or sched == "matched"
            ax.annotate(f"draw {n}", (48, ys[0]), xytext=(6, 1.5 if up else -2), textcoords="offset points",
                        fontsize=6.5, color=C["ink2"], va="bottom" if up else "top", ha="left")
        ax.set_ylim(70, 99)
        ax.set_xscale("log", base=2); ax.set_xticks([48, 96, 144, 240]); ax.set_xticklabels(["48", "96", "144", "240"]); ax.minorticks_off()
        ax.set_xlim(42, 270); ax.set_xlabel("cells in the training policy"); ax.set_title(title); ygrid(ax)
    axes[1][0].set_ylabel("exact match, common K48r test (%)")
    fig.legend(handles=[Line2D([], [], color=col[256], marker="o", ms=4.5, label="d = 256"), Line2D([], [], color=col[384], marker="o", ms=4.5, label="d = 384"),
                        Line2D([], [], color=C["blue"], lw=1.0, ls=(0, (4, 2)), label="d = 384, draws 2 and 3"),
                        Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], label="five seeds"),
                        Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], markerfacecolor="white", label="three seeds")],
               loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.0))
    save(fig, "Figure04_shared_action_accuracy")


# ---------------------------------------------------------------- Fig 5: per-action exposure
def fig5():
    P = json.loads((HERE / "analysis/per_action_exposure/per_action_exposure.json").read_text(encoding="utf-8"))
    rows = P["cells"]; x = np.array([r["train_rows"] for r in rows])
    low = np.argsort(x, kind="stable")[:5]
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.7), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, name, title in zip(axes, ("development", "unseen_frames"), ("(a) Development test", "(b) Unseen-frame hold-out")):
        y = np.array([r[name]["exact_mean"] for r in rows]); lo = np.array([r[name]["ci90"][0] for r in rows]); hi = np.array([r[name]["ci90"][1] for r in rows])
        ax.vlines(x, np.clip(lo, 0, 100), np.clip(hi, 0, 100), color=C["pale"], lw=0.5, alpha=0.7, zorder=2)
        ax.scatter(x, y, s=7, color=C["blue"], lw=0, zorder=3)
        ax.scatter(x[low], y[low], s=42, facecolors="none", edgecolors=C["red"], linewidths=1.1, zorder=4)
        ax.set_xscale("log"); ax.set_xticks([20, 50, 100, 200, 300]); ax.set_xticklabels(["20", "50", "100", "200", "300"]); ax.minorticks_off()
        ax.set_ylim(-3, 103); ax.set_xlabel("training rows for the cell (log scale)"); ax.set_title(title); ax.grid(zorder=0); ax.set_axisbelow(True)
        ax.text(0.03, 0.04, f"Spearman ρ = {P['summary'][name]['spearman_rho_exposure_vs_exact']:+.2f}".replace("-", "−"), transform=ax.transAxes, fontsize=7, color=C["ink2"])
    axes[0].set_ylabel("exact tuple match (%)")
    fig.legend(handles=[Line2D([], [], marker="o", lw=0, ms=3, color=C["blue"], label="policy cell, five-seed mean"),
                        Line2D([], [], color=C["pale"], lw=1, label="90% t interval"),
                        Line2D([], [], marker="o", lw=0, ms=6, color=C["red"], markerfacecolor="none", label="five least-exposed cells")],
               loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.06))
    save(fig, "Figure05_per_action_exposure")


# ---------------------------------------------------------------- Fig 6: width, depth, vocabulary
def fig6():
    fig = plt.figure(figsize=(W, 6.6))
    gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.32)
    # (a) width under the 24k tokenizer
    ax = fig.add_subplot(gs[0, 0]); t = sorted(table("scale_grid_width"), key=lambda r: r["d_model"])
    ax.plot([r["d_model"] for r in t], [r["exact_mean"] for r in t], color=C["blue"], zorder=3)
    for r in t: per_seed_dots(ax, r["d_model"], r, C["blue"]); mark(ax, r["d_model"], r["exact_mean"], C["blue"], len(r["seeds"]) >= 5)
    ax.axvline(240, color=C["grey"], lw=0.8, ls=(0, (3, 2)), zorder=1); ax.text(300, 47, "K_eff = 240", fontsize=6.5, color=C["ink2"])
    ax.set_xscale("log", base=2); ax.set_xticks([r["d_model"] for r in t]); ax.set_xticklabels([("\n" if r["d_model"] == 224 else "") + str(r["d_model"]) for r in t]); ax.minorticks_off()
    ax.tick_params(axis="x", labelsize=6.8); ax.set_ylim(44, 92)
    ax.set_xlabel("hidden size d (L = 8, 24k tokenizer)"); ax.set_ylabel("exact tuple match (%)"); ax.set_title("(a) Width"); ygrid(ax)
    # (b) depth accuracy, two policies
    ax = fig.add_subplot(gs[0, 1])
    for roots, col in ((("scale_grid_depth", "scale_grid_depth_l3"), C["blue"]), (("scale_grid_depth_a2", "scale_grid_depth_a2_l3"), C["aqua"])):
        t = sorted(table(roots[0]) + table(roots[1]), key=lambda r: r["d_model"])
        ax.plot([r["d_model"] for r in t], [r["exact_mean"] for r in t], color=col, zorder=3)
        for r in t: per_seed_dots(ax, r["d_model"], r, col); mark(ax, r["d_model"], r["exact_mean"], col, len(r["seeds"]) >= 5)
    ax.set_xticks([2, 3, 4, 6, 8, 12, 16]); ax.set_ylim(50, 95); ax.set_xlabel("layers L (d = 384, 24k tokenizer)"); ax.set_title("(b) Depth: accuracy"); ygrid(ax)
    ax.legend(handles=[Line2D([], [], color=C["blue"], marker="o", ms=4, label="A = 3, K_eff 240 (production)"),
                       Line2D([], [], color=C["aqua"], marker="o", ms=4, label="A = 2, K_eff 192 (control)")], loc="lower right", fontsize=6.5)
    # (c) depth latency
    ax = fig.add_subplot(gs[1, 0]); t = sorted(table("scale_grid_depth") + table("scale_grid_depth_l3"), key=lambda r: r["d_model"])
    ax.plot([r["d_model"] for r in t], [r["latency_ms"] for r in t], color=C["blue"], marker="o", ms=4, markeredgecolor="white", zorder=3)
    ax.set_xticks([2, 3, 4, 6, 8, 12, 16]); ax.set_ylim(0, 450); ax.set_xlabel("layers L"); ax.set_ylabel("reference-decoder latency (ms)")
    ax.set_title("(c) Depth: latency (fp32, no KV cache)"); ygrid(ax)
    # (d) vocabulary accuracy
    names = ["V4k", "V8k", "V16k", "V24k"]; sizes = [4000, 8000, 16000, 24000]
    v2 = {n: table(f"scale_grid_vocab_natural/{n}")[0] for n in names}; v1 = {n: table(f"scale_grid_vocab/{n}")[0] for n in names}
    prod = [r for r in table("scale_grid_width") if r["scale"] == "W384"][0]
    ax = fig.add_subplot(gs[1, 1])
    ax.plot(sizes, [v1[n]["exact_mean"] for n in names], color=C["grey"], marker="o", ms=3.5, markeredgecolor="white", zorder=2)
    ax.plot(sizes, [v2[n]["exact_mean"] for n in names], color=C["aqua"], zorder=3)
    for s, n in zip(sizes, names):
        c = C["orange"] if n == "V4k" else C["aqua"]
        per_seed_dots(ax, s, v2[n], c); mark(ax, s, v2[n]["exact_mean"], c, len(v2[n]["seeds"]) >= 5, z=5)
    ax.scatter([24000], [prod["exact_mean"]], marker="D", s=26, color=C["blue"], edgecolors="white", linewidths=0.8, zorder=6)
    ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(["4k", "8k", "16k", "24k"]); ax.minorticks_off(); ax.set_ylim(40, 95)
    ax.set_xlabel("vocabulary size (d = 384, L = 8)"); ax.set_title("(d) Vocabulary: accuracy"); ygrid(ax)
    # (e) rare-token exposure
    freq = json.loads((A / "scale_grid_vocab_natural/test_token_frequency_diagnostic.json").read_text(encoding="utf-8"))
    ax = fig.add_subplot(gs[2, 0]); share = [100 * freq[f"V2 {n}"]["test_lt100"] for n in names]
    ax.plot(sizes, share, color=C["aqua"], zorder=3)
    for s, v, n in zip(sizes, share, names): ax.scatter([s], [v], s=22, color=C["orange"] if n == "V4k" else C["aqua"], edgecolors="white", linewidths=0.8, zorder=4)
    ax.scatter([24000], [100 * freq["orig24k"]["test_lt100"]], marker="D", s=26, color=C["blue"], edgecolors="white", linewidths=0.8, zorder=6)
    ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(["4k", "8k", "16k", "24k"]); ax.minorticks_off(); ax.set_ylim(0, 20)
    ax.set_xlabel("vocabulary size"); ax.set_ylabel("test tokens seen < 100× (%)"); ax.set_title("(e) Vocabulary: rare-token exposure"); ygrid(ax)
    # key in the free cell
    ax = fig.add_subplot(gs[2, 1]); ax.set_axis_off()
    ax.legend(handles=[Line2D([], [], color=C["blue"], marker="D", lw=0, ms=4.5, label="production 24k tokenizer"),
                       Line2D([], [], color=C["aqua"], marker="o", ms=4.5, label="natural-corpus tokenizers"),
                       Line2D([], [], color=C["orange"], marker="o", lw=0, ms=4.5, label="selected 4k natural tokenizer"),
                       Line2D([], [], color=C["grey"], marker="o", ms=4, label="template-corpus tokenizers\n(negative control)"),
                       Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], label="five-seed mean"),
                       Line2D([], [], marker="o", lw=0, ms=4.5, color=C["ink2"], markerfacecolor="white", label="three-seed mean"),
                       Line2D([], [], marker="o", lw=0, ms=2.6, color=C["ink2"], alpha=0.4, label="individual seed")],
              loc="center left", fontsize=7, labelspacing=0.75)
    save(fig, "Figure06_width_depth_vocabulary")


# ---------------------------------------------------------------- Fig 7: depth Pareto
def fig7():
    D = json.loads((HERE / "analysis/depth_pareto/depth_pareto.json").read_text(encoding="utf-8"))
    col = {"A=3, K_eff 240 (production)": C["blue"], "A=2, K_eff 192 (control)": C["aqua"], "A=3, K_eff 240, 4k tokenizer (selected)": C["orange"]}
    lab = {"A=3, K_eff 240 (production)": "A = 3, K_eff 240, 24k tokenizer", "A=2, K_eff 192 (control)": "A = 2, K_eff 192, 24k tokenizer (control)",
           "A=3, K_eff 240, 4k tokenizer (selected)": "A = 3, K_eff 240, 4k tokenizer (selected)"}
    # label offsets in points, chosen so no label sits on another label or marker
    off = {("A=3, K_eff 240 (production)", 2): (-4, -12), ("A=3, K_eff 240 (production)", 3): (5, -11), ("A=3, K_eff 240 (production)", 4): (6, -10),
           ("A=3, K_eff 240 (production)", 6): (6, -9), ("A=3, K_eff 240 (production)", 8): (6, -9), ("A=3, K_eff 240 (production)", 12): (6, 4),
           ("A=3, K_eff 240 (production)", 16): (6, 4), ("A=2, K_eff 192 (control)", 2): (-17, -3), ("A=2, K_eff 192 (control)", 3): (-17, 3),
           ("A=2, K_eff 192 (control)", 4): (-6, 8), ("A=2, K_eff 192 (control)", 6): (6, 3), ("A=2, K_eff 192 (control)", 8): (7, 2),
           ("A=3, K_eff 240, 4k tokenizer (selected)", 4): (-12, 11), ("A=3, K_eff 240, 4k tokenizer (selected)", 8): (-8, 9)}
    fig, ax = plt.subplots(figsize=(W * 0.82, 3.3))
    for name, pts in D.items():
        c = col[name]; x = [p["latency_ms"] for p in pts]; y = [p["exact"] for p in pts]
        ax.errorbar(x, y, yerr=[p["sd"] for p in pts], color=c, ecolor=c, elinewidth=0.8, lw=1.2, alpha=0.9, zorder=3, label=lab[name])
        for p in pts:
            mark(ax, p["latency_ms"], p["exact"], c, p["seeds"] >= 5, s=18, z=5)
            if p["pareto"]: ax.scatter([p["latency_ms"]], [p["exact"]], s=70, facecolors="none", edgecolors=c, linewidths=1.0, zorder=4)
            dx, dy = off[(name, p["L"])]
            ax.annotate(f"L{p['L']}", (p["latency_ms"], p["exact"]), textcoords="offset points", xytext=(dx, dy), fontsize=6.5, color=c,
                        ha="right" if dx < 0 else "left", va="center")
    ax.set_xlim(50, 440); ax.set_ylim(60, 92)
    ax.set_xlabel("reference-decoder latency (ms, fp32, no KV cache)"); ax.set_ylabel("development exact tuple match (%)"); ax.grid(zorder=0); ax.set_axisbelow(True)
    h, l = ax.get_legend_handles_labels()
    h += [Line2D([], [], marker="o", lw=0, ms=7.5, color=C["ink2"], markerfacecolor="none", label="undominated in its series"),
          Line2D([], [], marker="o", lw=0, ms=4, color=C["ink2"], markerfacecolor="white", label="three seeds (others five)")]
    ax.legend(handles=h, loc="lower right", fontsize=6.5)
    save(fig, "Figure07_depth_pareto")


# ---------------------------------------------------------------- Fig 8: accuracy vs parameters
def fig8():
    cells = []
    def add(root, scale, label, tok):
        r = [t for t in table(root) if t["scale"] == scale][0]
        cells.append({"label": label, "tok": tok, "params": r["params"] / 1e6, "exact": r["exact_mean"], "sd": r["exact_sd"], "n": len(r["seeds"])})
    for d in (128, 192, 224, 256, 320, 384, 512): add("scale_grid_width", f"W{d}", f"d{d} L8 V24k", "24k")
    for L in (2, 4, 6, 12, 16): add("scale_grid_depth", f"D{L}", f"d384 L{L} V24k", "24k")
    for d in (224, 256, 320): add("scale_grid_width_v4k", f"X{d}", f"d{d} L8 V4k", "4k")
    add("scale_grid_vocab_natural/V4k", "V4k", "selected", "4k"); add("scale_grid_combo", "C4kL4", "d384 L4 V4k", "4k")
    for v in ("V8k", "V16k", "V24k"): add(f"scale_grid_vocab_natural/{v}", v, f"d384 L8 {v} natural", "nat")
    col = {"24k": C["blue"], "4k": C["orange"], "nat": C["aqua"]}
    fig, ax = plt.subplots(figsize=(W * 0.82, 3.3))
    for c in cells:
        ax.errorbar(c["params"], c["exact"], yerr=c["sd"], fmt="none", ecolor=col[c["tok"]], elinewidth=0.8, alpha=0.75, zorder=2)
        mark(ax, c["params"], c["exact"], col[c["tok"]], c["n"] >= 5, s=26)
    def note(label, text, xy_text, ha="left"):
        c = [c for c in cells if c["label"] == label][0]
        ax.annotate(text, (c["params"], c["exact"]), xytext=xy_text, textcoords="data", fontsize=6.8, ha=ha, va="center",
                    arrowprops={"arrowstyle": "-", "color": C["ink2"], "lw": 0.6, "shrinkA": 1, "shrinkB": 4})
    note("selected", "selected\nd384 L8 V4k", (20.5, 91.5))
    note("d384 L8 V24k", "deployed architecture\nd384 L8 V24k", (27.0, 55.5), ha="center")
    note("d256 L8 V4k", "d256 L8 V4k\n(dominated)", (5.0, 64.5), ha="center")
    ax.set_xscale("log"); ax.set_xticks([4, 8, 16, 32]); ax.set_xticklabels(["4M", "8M", "16M", "32M"]); ax.minorticks_off(); ax.set_xlim(3.6, 45)
    ax.set_ylim(40, 95); ax.set_xlabel("parameters (log scale)"); ax.set_ylabel("development exact tuple match (%)"); ygrid(ax)
    ax.legend(handles=[Line2D([], [], marker="o", lw=0, ms=5, color=C["blue"], label="24k production tokenizer"),
                       Line2D([], [], marker="o", lw=0, ms=5, color=C["orange"], label="4k natural tokenizer"),
                       Line2D([], [], marker="o", lw=0, ms=5, color=C["aqua"], label="8k/16k/24k natural tokenizers"),
                       Line2D([], [], marker="o", lw=0, ms=5, color=C["ink2"], markerfacecolor="white", label="three seeds (others five)")],
              loc="lower right", fontsize=6.5)
    save(fig, "Figure08_accuracy_vs_parameters")


# ---------------------------------------------------------------- Fig 9: four distributions
def fig9():
    R = json.loads((HERE / "analysis/audited_requests_eval.json").read_text(encoding="utf-8"))["families"]
    fams = ("selected_fp32", "reference_24k", "head240")
    col = {"selected_fp32": C["orange"], "reference_24k": C["blue"], "head240": C["aqua"]}
    name = {"selected_fp32": "selected generative decoder (15.7M)", "reference_24k": "retrained deployed architecture (23.4M)", "head240": "size-matched 240-class head (15.8M)"}
    fig, axes = plt.subplots(1, 2, figsize=(W, 3.0), gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.2})
    ax = axes[0]; dx = {"selected_fp32": -0.09, "reference_24k": 0.0, "head240": 0.09}
    for l in fams:
        ys = [PAPER[l]["development"], PAPER[l]["unseen frames"], R[l]["exact"]["mean"], PAPER[l]["stress"]]
        es = [PAPER_SD[l]["development"], PAPER_SD[l]["unseen frames"], R[l]["exact"]["sd"], PAPER_SD[l]["stress"]]
        xs = [i + dx[l] for i in range(4)]
        ax.errorbar(xs, ys, yerr=es, color=col[l], ecolor=col[l], elinewidth=0.9, marker="o", ms=4, markeredgecolor="white", zorder=3, label=name[l])
    ax.set_xticks(range(4)); ax.set_xticklabels(["development\n(templates)", "unseen\nframes", "audited\nrequests", "machine\nparaphrases"], fontsize=7)
    ax.set_xlim(-0.3, 3.3); ax.set_ylim(0, 100); ax.set_ylabel("exact tuple match (%)"); ax.set_title("(a) Four constructed input distributions"); ygrid(ax)
    ax.legend(loc="upper right", fontsize=6.5)
    ax = axes[1]; w = 0.36
    for k, l in enumerate(("selected_fp32", "head240")):
        f = R[l]["by_variation"]; ys = [f[v]["mean"] for v in SOURCES]; es = [f[v]["sd"] for v in SOURCES]
        xs = np.arange(4) + (k - 0.5) * w
        ax.bar(xs, ys, w * 0.92, color=col[l], zorder=2, label=name[l].split(" (")[0])
        ax.errorbar(xs, ys, yerr=es, fmt="none", ecolor=C["ink"], elinewidth=0.8, zorder=3)
        for x, y, e in zip(xs, ys, es): ax.text(x, y + e + 1.5, f"{y:.1f}", ha="center", fontsize=5.8, color=C["ink2"])
    ax.set_xticks(range(4)); ax.set_xticklabels(["plain\n(120)", "negated\n(40)", "altered\norder\n(40)", "context\nclause\n(40)"], fontsize=7)
    ax.set_ylim(0, 100); ax.set_title("(b) Audited requests by form"); ygrid(ax); ax.legend(loc="upper right", fontsize=6.5)
    save(fig, "Figure09_four_distributions")


# ---------------------------------------------------------------- Fig 10: quantization pairs
def fig10():
    rows = list(csv.DictReader((PKG / "plots/data/F08_quantization_equivalence.csv").open(encoding="utf-8")))
    models = list(dict.fromkeys(r["model"] for r in rows))
    titles = {models[0]: "(a) Selected model d384 L8 V4k (15.7M)", models[1]: "(b) d384 L4 V4k (8.6M)"}
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.3), sharey=True, gridspec_kw={"wspace": 0.12})
    for ax, m in zip(axes, models):
        rs = [r for r in rows if r["model"] == m]
        for i, r in enumerate(rs):
            a, b = float(r["fp32_exact"]), float(r["mixed_bit_exact"])
            ax.plot([a, b], [i, i], color=C["grid"], lw=2.2, zorder=1, solid_capstyle="round")
            ax.scatter([a], [i], s=26, color=C["blue"], edgecolors="white", linewidths=0.8, zorder=3)
            ax.scatter([b], [i], s=26, color=C["orange"], edgecolors="white", linewidths=0.8, zorder=3)
        d = np.mean([float(r["delta_pp"]) for r in rs])
        ax.set_yticks(range(len(rs))); ax.set_yticklabels([f"seed {r['seed']}" for r in rs]); ax.set_ylim(-0.6, len(rs) - 0.4)
        ax.set_xlabel("development exact tuple match (%)"); ax.set_title(titles[m]); ygrid(ax, "x")
        ax.text(0.98, 0.04, f"mean difference {d:+.2f} pp".replace("-", "−"), transform=ax.transAxes, ha="right", fontsize=6.8, color=C["ink2"])
    axes[1].set_xlim(74, 91)
    fig.legend(handles=[Line2D([], [], marker="o", lw=0, ms=5, color=C["blue"], label="fp32"), Line2D([], [], marker="o", lw=0, ms=5, color=C["orange"], label="mixed 4/6/8-bit")],
               loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.08))
    save(fig, "Figure10_quantization_pairs")


# ---------------------------------------------------------------- Fig 11: CPU deployment
def fig11():
    rows = list(csv.DictReader((PKG / "plots/data/F09_cpu_deployment.csv").open(encoding="utf-8")))
    y = list(range(len(rows)))[::-1]; cols = [C["orange"] if "selected" in r["model"] else C["blue"] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.3), sharey=True, gridspec_kw={"width_ratios": [1.25, 1, 0.8], "wspace": 0.2})
    ax = axes[0]
    for yi, r, c in zip(y, rows, cols):
        ax.plot([float(r["median_ms"]), float(r["p95_ms"])], [yi, yi], color=c, lw=1.6, zorder=2)
        ax.scatter([float(r["median_ms"])], [yi], s=26, color=c, edgecolors="white", linewidths=0.8, zorder=3)
        ax.scatter([float(r["p95_ms"])], [yi], s=26, facecolors="white", edgecolors=c, linewidths=1.0, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([r["model"] for r in rows], fontsize=7); ax.set_xlim(0, 130)
    ax.set_xlabel("ms: median ● to p95 ○"); ax.set_title("(a) CPU latency, 4 threads"); ygrid(ax, "x")
    for ax, key, xl, lim, title, fmt in ((axes[1], "file_mb", "MB (fp32: weights only)", 80, "(b) Size on disk", "{:.1f}"),
                                         (axes[2], "load_s", "seconds", 0.27, "(c) Loading", "{:.2f}")):
        v = [float(r[key]) for r in rows]
        ax.barh(y, v, height=0.55, color=cols, zorder=2)
        for yi, s in zip(y, v): ax.text(s + lim * 0.02, yi, fmt.format(s), va="center", fontsize=6.5, color=C["ink2"])
        ax.set_xlim(0, lim); ax.set_xlabel(xl); ax.set_title(title); ygrid(ax, "x"); ax.tick_params(axis="y", length=0)
    save(fig, "Figure11_cpu_deployment")


if __name__ == "__main__":
    for f in (fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11):
        f()
