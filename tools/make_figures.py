"""Generate every figure of the SentiLight capacity-search paper from the repository's analysis files.

Outputs (in this directory): F##_<name>.png (300 dpi), F##_<name>.pdf, data/F##_<name>.csv (the plotted numbers),
and README.md (figure list with sources). Re-running regenerates everything deterministically.

Design rules (dataviz method): one axis per plot (no dual axes); categorical hues in fixed validated order
(blue, orange, aqua, yellow, magenta); ordered quantities (K_eff) on a single-hue sequential ramp; 2 px lines,
>= 8 px markers with a surface ring, hairline solid grid, legend for >= 2 series, sparse direct labels;
five-seed cells drawn filled, three-seed cells hollow. Only final (five-seed where available) results are
plotted; no process narrative.
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "Implement_New_Android_v6"
R = REPO / "backend" / "reports"
DATA = HERE / "data"; DATA.mkdir(exist_ok=True)

# ---- palette (validated reference instance, light mode) ----
C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "yellow": "#eda100", "magenta": "#e87ba4",
     "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#8a8985", "grid": "#e6e5e1", "surface": "#fcfcfb", "red": "#e34948"}
SEQ = {"48": "#86b6ef", "240": "#5598e7", "480": "#256abf", "960": "#104281"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "axes.edgecolor": C["ink2"], "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
                     "xtick.color": C["ink2"], "ytick.color": C["ink2"], "text.color": C["ink"], "axes.labelcolor": C["ink"],
                     "grid.color": C["grid"], "grid.linewidth": 0.8, "grid.linestyle": "-", "legend.frameon": False,
                     "figure.facecolor": C["surface"], "axes.facecolor": C["surface"], "savefig.facecolor": C["surface"]})
DIMS = ("H", "S", "B", "Dimmer", "CT")
FIGS: list[tuple[str, str, str]] = []


def save(fig, name: str, caption: str, rows: list[dict], source: str):
    fig.savefig(HERE / f"{name}.png", dpi=300, bbox_inches="tight"); fig.savefig(HERE / f"{name}.pdf", bbox_inches="tight"); plt.close(fig)
    if rows:
        with (DATA / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            fields: list[str] = []
            for r in rows:
                for k in r.keys():
                    if k not in fields: fields.append(k)
            w = csv.DictWriter(f, fieldnames=fields, restval=""); w.writeheader(); w.writerows(rows)
    FIGS.append((name, caption, source)); print("wrote", name)


def table(root: str) -> list[dict]:
    return json.loads((R / root / "width_analysis.json").read_text(encoding="utf-8"))["table"]


def exact_from_per_row(p: Path) -> float:
    n = ok = 0
    for l in p.open(encoding="utf-8"):
        r = json.loads(l); n += 1; pr, ref = r.get("predicted"), r["reference"]
        ok += bool(pr) and all(int(pr[k]) == int(ref[k]) for k in DIMS)
    return 100 * ok / n


def series_plot(ax, xs, means, sds, per_seed, color, label, hollow_if_three=True, x_is_log=False):
    """mean line + per-seed dots (filled when >= 5 seeds, hollow when 3)."""
    ax.plot(xs, means, color=color, lw=2, solid_capstyle="round", label=label, zorder=3)
    for x, ps in zip(xs, per_seed):
        vals = list(ps.values()); five = len(vals) >= 5
        ax.scatter([x] * len(vals), vals, s=22, facecolors=color if (five or not hollow_if_three) else C["surface"],
                   edgecolors=color, linewidths=1.2, zorder=4, alpha=0.9)
    ax.scatter(xs, means, s=46, color=color, edgecolors=C["surface"], linewidths=1.5, zorder=5)


def grid(ax):
    ax.grid(axis="y", zorder=0); ax.set_axisbelow(True)


# ======================================================================
# F1 Width series under the production 24k tokenizer
def f1():
    t = table("scale_grid_width"); t = sorted(t, key=lambda r: r["d_model"])
    xs = [r["d_model"] for r in t]; m = [r["exact_mean"] for r in t]; sd = [r["exact_sd"] for r in t]; ps = [r["per_seed"] for r in t]
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    series_plot(ax, xs, m, sd, [{k: v["exact"] for k, v in p.items()} for p in ps], C["blue"], "exact tuple match")
    ax.axvline(240, color=C["muted"], lw=1, zorder=1); ax.text(244, 52, "K_eff = 240", color=C["ink2"], fontsize=8, va="bottom")
    ax.set_xlabel("hidden size d (L = 8, V = 24k production tokenizer)"); ax.set_ylabel("exact tuple match (%)")
    ax.set_xticks(xs); ax.set_ylim(45, 95); grid(ax)
    ax.legend(handles=[Line2D([], [], marker="o", color=C["blue"], lw=0, ms=6, label="five seeds"),
                       Line2D([], [], marker="o", color=C["blue"], markerfacecolor=C["surface"], lw=0, ms=6, label="three seeds"),
                       Line2D([], [], color=C["blue"], lw=2, label="seed mean")], loc="lower right", fontsize=8)
    rows = [{"d_model": r["d_model"], "params": r["params"], "n_seeds": len(r["seeds"]), "exact_mean": round(r["exact_mean"], 2), "exact_sd": round(r["exact_sd"], 2),
             "coarse_mean": round(r["coarse_mean"], 2), "strict_mean": round(r["strict_mean"], 2), **{f"exact_seed{s}": round(v["exact"], 2) for s, v in r["per_seed"].items()}} for r in t]
    save(fig, "F01_width_series_24k", "Width series (L = 8, production 24k tokenizer): exact tuple match vs hidden size. The largest reliable five-seed gain lies between d = 224 and 256, an interval that brackets K_eff = 240. Dots are individual seeds (filled = five-seed confirmatory cells, hollow = three-seed screening cells).", rows, "backend/reports/scale_grid_width/width_analysis.json")


# F2 K_eff series: fixed steps (a), fixed epochs (b), absolute-level knee (c)
def f2():
    fs = json.loads((R / "scale_grid_keff_fs" / "keff_analysis.json").read_text(encoding="utf-8"))
    fe = json.loads((R / "scale_grid_keff" / "keff_analysis_fixed_epochs.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), gridspec_kw={"width_ratios": [1, 1, 0.8]})
    rows = []
    for ax, res, title in ((axes[0], fs, "(a) fixed step budget (~3,100 SFT steps)"), (axes[1], fe, "(b) fixed epochs (4)")):
        for k in ("48", "240", "480", "960"):
            tb = sorted(res["columns"][k]["table"], key=lambda r: r["d_model"]); tb = [r for r in tb if r["d_model"] in (128, 192, 256, 384, 512)]
            xs = [r["d_model"] for r in tb]; ys = [r["exact_mean"] for r in tb]
            ax.plot(xs, ys, color=SEQ[k], lw=2, marker="o", ms=6, markeredgecolor=C["surface"], markeredgewidth=1.2, label=f"K_eff = {k}")
            ax.text(xs[-1] + 8, ys[-1], k, color=C["ink2"], fontsize=8, va="center")
            for r in tb: rows.append({"condition": title[4:].split(" (")[0], "k_eff": k, "d_model": r["d_model"], "exact_mean": round(r["exact_mean"], 2), "exact_sd": round(r["exact_sd"], 2), "n_seeds": len(r["seeds"])})
        ax.set_xticks([128, 192, 256, 384, 512]); ax.set_xlim(110, 560); ax.set_ylim(0, 95); ax.set_xlabel("hidden size d (L = 8)"); ax.set_title(title, loc="left"); grid(ax)
    axes[0].set_ylabel("exact tuple match (%)"); axes[0].legend(fontsize=8, loc="lower right", title="policy size")
    # (c) smallest d reaching 60 % exact vs K_eff (fixed steps)
    ax = axes[2]; kn = fs["absolute_knees"]; ks = [48, 240, 480, 960]; ds = [kn[str(k)]["60"] for k in ks]
    ax.plot(ks, ds, color=C["blue"], lw=2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2)
    sl = fs["absolute_slopes"]["60"]["slope"]
    ax.set_xscale("log", base=2); ax.set_yscale("log", base=2); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.set_yticks([128, 192, 256, 384, 512]); ax.set_yticklabels(["128", "192", "256", "384", "512"])
    ax.set_xlabel("K_eff (reachable actions)"); ax.set_ylabel("smallest d reaching 60 % exact"); ax.set_title(f"(c) knee vs K_eff, fixed steps (log–log slope {sl:.2f})", loc="left"); grid(ax)
    for k, d in zip(ks, ds): rows.append({"condition": "knee60", "k_eff": k, "d_model": d, "exact_mean": "", "exact_sd": "", "n_seeds": 3})
    save(fig, "F02_keff_series", "K_eff series (nested policies 48/240/480/960; d ∈ {128…512}, L = 8): (a) fixed SFT step budget, (b) fixed epochs (matched exposure per action), (c) smallest tested d reaching 60 % exact vs K_eff under fixed steps. Filled markers are five-seed cells (K240 column; threshold-crossing cells under fixed steps; K480/K960 at d = 384/512 under matched exposure), hollow markers three-seed screening cells. The 60 % threshold is a post hoc descriptive threshold. Slope 1 would mean d̂ ∝ K_eff.", rows, "backend/reports/scale_grid_keff_fs/keff_analysis.json; scale_grid_keff/keff_analysis_fixed_epochs.json")


# F3 Depth series: accuracy (a) and latency (b) — separate panels, one axis each
def f3():
    t = sorted(table("scale_grid_depth") + table("scale_grid_depth_l3"), key=lambda r: r["d_model"])  # d_model holds n_layer here
    L = [r["d_model"] for r in t]; ex = [r["exact_mean"] for r in t]; lat = [r["latency_ms"] for r in t]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
    series_plot(axes[0], L, ex, None, [{k: v["exact"] for k, v in r["per_seed"].items()} for r in t], C["blue"], "A = 3 attributes, K_eff 240 (production policy)")
    a2 = sorted(table("scale_grid_depth_a2") + table("scale_grid_depth_a2_l3"), key=lambda r: r["d_model"])
    series_plot(axes[0], [r["d_model"] for r in a2], [r["exact_mean"] for r in a2], None, [{k: v["exact"] for k, v in r["per_seed"].items()} for r in a2], C["orange"], "A = 2 attributes, K_eff 192 (control policy)")
    axes[0].set_xlabel("layers L (d = 384, V = 24k)"); axes[0].set_ylabel("exact tuple match (%)"); axes[0].set_xticks(L); axes[0].set_ylim(60, 95); axes[0].set_title("(a) accuracy", loc="left"); grid(axes[0]); axes[0].legend(fontsize=7.5, loc="lower right", bbox_to_anchor=(1.0, 0.02))
    axes[0].axvspan(3, 4, color=C["muted"], alpha=0.15, lw=0, zorder=0); axes[0].text(4.7, 94.2, "L = 2 → 4: +12.6 pp at A = 2 (5/5 seeds),\n+4.4 pp at A = 3 (4/5); no single adjacent step\nwithin L = 2..4 resolved at five seeds;\nno reliable adjacent gain detected above L = 4", color=C["ink2"], fontsize=7, va="top")
    axes[1].plot(L, lat, color=C["orange"], lw=2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2)
    axes[1].set_xlabel("layers L"); axes[1].set_ylabel("reference-decoder latency (ms)"); axes[1].set_xticks(L); axes[1].set_ylim(0, 450); axes[1].set_title("(b) latency, ~26 ms per layer (96 steps, no KV cache)", loc="left"); grid(axes[1])
    rows = [{"policy": "A=3 K240", "n_layer": r["d_model"], "params": r["params"], "n_seeds": len(r["seeds"]), "exact_mean": round(r["exact_mean"], 2), "exact_sd": round(r["exact_sd"], 2), "coarse_mean": round(r["coarse_mean"], 2), "latency_ms": round(r["latency_ms"], 1)} for r in t] + \
           [{"policy": "A=2 K192", "n_layer": r["d_model"], "params": r["params"], "n_seeds": len(r["seeds"]), "exact_mean": round(r["exact_mean"], 2), "exact_sd": round(r["exact_sd"], 2), "coarse_mean": round(r["coarse_mean"], 2), "latency_ms": round(r["latency_ms"], 1)} for r in a2]
    save(fig, "F03_depth_series", "Depth series (d = 384, V = 24k): (a) exact tuple match for the production policy (A = 3, K_eff 240) and the attribute-count control policy (A = 2, K_eff 192); L = 2, 3, 4 five seeds (42–46), deeper models three. Open markers are individual seeds. L = 2 could not provide consistently reliable performance across the two policies (L = 2 → 4: +12.6 pp at A = 2, 5/5 seeds; +4.4 pp at A = 3, 4/5), but whether the gain arises between L = 2 and 3 or between 3 and 4 was not resolved and the policy × depth interactions are imprecise, so the L = 3 sufficiency predicted by L = A + 1 at A = 2 is neither supported nor excluded. No reliable adjacent gain was detected above L = 4; equivalence among deeper configurations is not established. Absolute levels are not comparable across policies. (b) Reference-decoder latency grows approximately linearly with depth.", rows, "backend/reports/scale_grid_depth{,_l3}/width_analysis.json; scale_grid_depth_a2{,_l3}/width_analysis.json")


# F4 Vocabulary series: accuracy vs vocabulary (a) and rare-token share (b)
def f4():
    vt = {}
    for v in ("V4k", "V8k", "V16k", "V24k"):
        vt[v] = table(f"scale_grid_vocab_natural/{v}")[0]
    v1 = {v: table(f"scale_grid_vocab/{v}")[0] for v in ("V4k", "V8k", "V16k", "V24k")}
    prod = [r for r in table("scale_grid_width") if r["scale"] == "W384"][0]
    freq = json.loads((R / "scale_grid_vocab_natural" / "test_token_frequency_diagnostic.json").read_text(encoding="utf-8"))
    sizes = [4000, 8000, 16000, 24000]; names = ["V4k", "V8k", "V16k", "V24k"]
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.4))
    ax = axes[0]
    series_plot(ax, sizes, [vt[n]["exact_mean"] for n in names], None, [{k: v["exact"] for k, v in vt[n]["per_seed"].items()} for n in names], C["blue"], "natural-corpus tokenizer (V2)")
    ax.plot(sizes, [v1[n]["exact_mean"] for n in names], color=C["muted"], lw=2, marker="o", ms=6, markeredgecolor=C["surface"], label="template-corpus tokenizer (V1, negative control)")
    ax.scatter([24000], [prod["exact_mean"]], marker="D", s=60, color=C["orange"], edgecolors=C["surface"], linewidths=1.2, zorder=6, label="production 24k tokenizer")
    ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(["4k", "8k", "16k", "24k"]); ax.set_xlabel("vocabulary size (d = 384, L = 8)"); ax.set_ylabel("exact tuple match (%)"); ax.set_ylim(40, 95); ax.set_title("(a) accuracy", loc="left"); grid(ax); ax.legend(fontsize=7.5, loc="lower left")
    ax = axes[1]
    share = [100 * freq[f"V2 {n}"]["test_lt100"] for n in names]
    ax.plot(sizes, share, color=C["blue"], lw=2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2, label="natural-corpus tokenizer (V2)")
    ax.scatter([24000], [100 * freq["orig24k"]["test_lt100"]], marker="D", s=60, color=C["orange"], edgecolors=C["surface"], linewidths=1.2, zorder=6, label="production 24k")
    ax.set_xscale("log", base=2); ax.set_xticks(sizes); ax.set_xticklabels(["4k", "8k", "16k", "24k"]); ax.set_xlabel("vocabulary size"); ax.set_ylabel("test tokens seen < 100× in pretraining (%)"); ax.set_ylim(0, 20); ax.set_title("(b) rare-token exposure", loc="left"); grid(ax); ax.legend(fontsize=7.5, loc="upper left")
    rows = [{"vocab": s, "V2_exact_mean": round(vt[n]["exact_mean"], 2), "V2_exact_sd": round(vt[n]["exact_sd"], 2), "V2_n_seeds": len(vt[n]["seeds"]), "V1_exact_mean": round(v1[n]["exact_mean"], 2),
             "V2_test_tokens_lt100_pct": round(sh, 2), "production24k_exact_mean": round(prod["exact_mean"], 2) if s == 24000 else "", "production24k_lt100_pct": round(100 * freq["orig24k"]["test_lt100"], 2) if s == 24000 else ""} for s, n, sh in zip(sizes, names, share)]
    save(fig, "F04_vocabulary_series", "Vocabulary series (d = 384, L = 8): (a) exact tuple match for tokenizers trained on the natural corpus (V2, five seeds at 4k, three otherwise), on the template-heavy corpus (V1, negative control) and the production 24k tokenizer (a different training corpus); (b) exploratory diagnostic: share of test tokens seen fewer than 100 times in pretraining (threshold chosen after the results), which tracks the accuracy ordering.", rows, "backend/reports/scale_grid_vocab_natural/*; scale_grid_vocab/*; test_token_frequency_diagnostic.json")


# F5 Budget robustness: 2,400 vs 4,800 steps for 4k and 24k natural tokenizers (slope chart)
def f5():
    v4 = table("scale_grid_vocab_natural/V4k")[0]; v24 = table("scale_grid_vocab_natural/V24k")[0]
    b4 = table("scale_grid_budget/B4k")[0]; b24 = table("scale_grid_budget/B24k")[0]
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    for a, b, col, lab in ((v4, b4, C["blue"], "V = 4k"), (v24, b24, C["orange"], "V = 24k")):
        ax.plot([2400, 4800], [a["exact_mean"], b["exact_mean"]], color=col, lw=2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2, label=lab)
        for x, r in ((2400, a), (4800, b)):
            vals = [v["exact"] for v in r["per_seed"].values()]; ax.scatter([x] * len(vals), vals, s=18, color=col, alpha=0.6, zorder=3)
        ax.text(4870, b["exact_mean"], f"{b['exact_mean']:.1f}", color=C["ink2"], fontsize=8, va="center")
    ax.set_xticks([2400, 4800]); ax.set_xlim(2100, 5400); ax.set_ylim(55, 95); ax.set_xlabel("pretraining steps (d = 384, L = 8)"); ax.set_ylabel("exact tuple match (%)"); grid(ax); ax.legend(fontsize=8, loc="center right")
    rows = [{"vocab": v, "steps": s, "exact_mean": round(r["exact_mean"], 2), "exact_sd": round(r["exact_sd"], 2), "n_seeds": len(r["seeds"])} for v, s, r in (("4k", 2400, v4), ("4k", 4800, b4), ("24k", 2400, v24), ("24k", 4800, b24))]
    save(fig, "F05_budget_robustness", "Doubling the pretraining step budget (2,400 → 4,800) for the 4k and 24k natural-corpus tokenizers; small dots are seeds. The 4k advantage narrows by 3 pp of 18.6.", rows, "backend/reports/scale_grid_budget/*; scale_grid_vocab_natural/*")


# F6 Tokenizer configuration × width
def f6():
    w = {r["d_model"]: r for r in table("scale_grid_width")}
    x = {r["d_model"]: r for r in table("scale_grid_width_v4k")}; x[384] = table("scale_grid_vocab_natural/V4k")[0]
    fig, ax = plt.subplots(figsize=(5.4, 3.5))
    ds24 = [192, 224, 256, 320, 384, 512]; ds4 = [224, 256, 320, 384]
    series_plot(ax, ds24, [w[d]["exact_mean"] for d in ds24], None, [{k: v["exact"] for k, v in w[d]["per_seed"].items()} for d in ds24], C["blue"], "production 24k tokenizer")
    series_plot(ax, ds4, [x[d]["exact_mean"] for d in ds4], None, [{k: v["exact"] for k, v in x[d]["per_seed"].items()} for d in ds4], C["orange"], "natural 4k tokenizer")
    ax.set_xticks(ds24); ax.set_xlabel("hidden size d (L = 8)"); ax.set_ylabel("exact tuple match (%)"); ax.set_ylim(60, 95); grid(ax); ax.legend(fontsize=8, loc="lower right")
    ax.text(384, 88.5, "selected: d = 384, V = 4k", color=C["ink2"], fontsize=8, ha="center")
    rows = [{"tokenizer": "24k", "d_model": d, "exact_mean": round(w[d]["exact_mean"], 2), "exact_sd": round(w[d]["exact_sd"], 2), "n_seeds": len(w[d]["seeds"])} for d in ds24] + \
           [{"tokenizer": "4k", "d_model": d, "exact_mean": round(x[d]["exact_mean"], 2), "exact_sd": round(x[d]["exact_sd"], 2), "n_seeds": len(x[d]["seeds"])} for d in ds4]
    save(fig, "F06_tokenizer_width_interaction", "Width–accuracy relationship under two tokenizer configurations (L = 8). Filled dots five seeds, hollow three. The 256 → 384 gain is +2.8 pp under the 24k tokenizer and +10.6 pp under the 4k tokenizer; the interaction (+7.8 pp) is suggestive, its seed-level interval includes zero.", rows, "backend/reports/scale_grid_width/*; scale_grid_width_v4k/*; scale_grid_vocab_natural/V4k/*")


# F7 Pareto: accuracy vs parameters for every five-seed cell (+ three-seed cells hollow)
def f7():
    cells = []
    def add(root, scale, label, tok):
        r = [t for t in table(root) if t["scale"] == scale][0]
        cells.append({"label": label, "tokenizer": tok, "params": r["params"], "exact_mean": r["exact_mean"], "exact_sd": r["exact_sd"], "n": len(r["seeds"])})
    for d in (128, 192, 224, 256, 320, 384, 512): add("scale_grid_width", f"W{d}", f"d{d} L8 V24k", "24k")
    for L in (2, 4, 6, 12, 16): add("scale_grid_depth", f"D{L}", f"d384 L{L} V24k", "24k")
    for d in (224, 256, 320): add("scale_grid_width_v4k", f"X{d}", f"d{d} L8 V4k", "4k")
    add("scale_grid_vocab_natural/V4k", "V4k", "d384 L8 V4k (selected)", "4k"); add("scale_grid_combo", "C4kL4", "d384 L4 V4k", "4k")
    for v in ("V8k", "V16k", "V24k"): add(f"scale_grid_vocab_natural/{v}", v, f"d384 L8 {v} natural", "4k-family")
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for c in cells:
        col = C["blue"] if c["tokenizer"] == "24k" else (C["orange"] if c["tokenizer"] == "4k" else C["aqua"])
        five = c["n"] >= 5
        ax.errorbar(c["params"] / 1e6, c["exact_mean"], yerr=c["exact_sd"], fmt="none", ecolor=col, elinewidth=1, capsize=2, alpha=0.7, zorder=2)
        ax.scatter(c["params"] / 1e6, c["exact_mean"], s=54, facecolors=col if five else C["surface"], edgecolors=col, linewidths=1.4, zorder=4)
    sel = [c for c in cells if "selected" in c["label"]][0]
    ax.annotate("selected\nd384 L8 V4k", (sel["params"] / 1e6, sel["exact_mean"]), xytext=(sel["params"] / 1e6 * 1.25, sel["exact_mean"] + 3), fontsize=8, color=C["ink"], arrowprops={"arrowstyle": "-", "color": C["ink2"], "lw": 0.8})
    dep = [c for c in cells if c["label"] == "d384 L8 V24k"][0]
    ax.annotate("deployed cfg\nd384 L8 V24k", (dep["params"] / 1e6, dep["exact_mean"]), xytext=(dep["params"] / 1e6 * 0.62, dep["exact_mean"] - 13), fontsize=8, color=C["ink"], arrowprops={"arrowstyle": "-", "color": C["ink2"], "lw": 0.8})
    x256 = [c for c in cells if c["label"] == "d256 L8 V4k"][0]
    ax.annotate("d256 V4k (dominated)", (x256["params"] / 1e6, x256["exact_mean"]), xytext=(x256["params"] / 1e6 * 0.55, x256["exact_mean"] - 8), fontsize=8, color=C["ink2"], arrowprops={"arrowstyle": "-", "color": C["ink2"], "lw": 0.8})
    ax.set_xscale("log"); ax.set_xticks([4, 8, 16, 32]); ax.set_xticklabels(["4M", "8M", "16M", "32M"]); ax.set_xlabel("parameters"); ax.set_ylabel("exact tuple match (%), mean ± SD over seeds"); ax.set_ylim(45, 95); grid(ax)
    ax.legend(handles=[Line2D([], [], marker="o", color=C["blue"], lw=0, ms=7, label="24k production tokenizer"), Line2D([], [], marker="o", color=C["orange"], lw=0, ms=7, label="4k natural tokenizer"),
                       Line2D([], [], marker="o", color=C["aqua"], lw=0, ms=7, label="8k/16k/24k natural tokenizers"), Line2D([], [], marker="o", color=C["ink2"], markerfacecolor=C["surface"], lw=0, ms=7, label="three seeds (hollow)")], fontsize=7.5, loc="lower right")
    rows = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in c.items()} for c in cells]
    save(fig, "F07_pareto_accuracy_parameters", "Accuracy–size landscape of all evaluated configurations (mean ± SD over seeds; filled = five seeds, hollow = three). The selected model (d 384, L 8, V 4k; 15.7M) and the deployed configuration (23.4M) are labelled; d 256 / V 4k is dominated by d 224 / V 4k.", rows, "all width_analysis.json files")


# F8 Quantization equivalence: fp32 vs mixed-bit per seed (paired dumbbells)
def f8():
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2), sharey=True)
    rows = []
    for ax, (fp_root, q_root, fp_tag, q_tag, title) in zip(axes, (("scale_grid_vocab_natural/V4k", "scale_grid_vocab_natural_q4", "V4k", "V4kq", "(a) selected model d384 L8 V4k (15.7M)"),
                                                                     ("scale_grid_combo", "scale_grid_combo_q4", "C4kL4", "C4kL4q", "(b) d384 L4 V4k (8.6M)"))):
        for i, s in enumerate((42, 43, 44, 45, 46)):
            a = exact_from_per_row(R / fp_root / "per_row" / f"compactlm_{fp_tag}_f100_s{s}.jsonl"); b = exact_from_per_row(R / q_root / "per_row" / f"compactlm_{q_tag}_f100_s{s}.jsonl")
            ax.plot([a, b], [i, i], color=C["grid"], lw=2, zorder=1)
            ax.scatter([a], [i], s=50, color=C["blue"], edgecolors=C["surface"], linewidths=1.2, zorder=3); ax.scatter([b], [i], s=50, color=C["orange"], edgecolors=C["surface"], linewidths=1.2, zorder=3)
            rows.append({"model": title.split(") ")[1], "seed": s, "fp32_exact": round(a, 2), "mixed_bit_exact": round(b, 2), "delta_pp": round(b - a, 2)})
        ax.set_yticks(range(5)); ax.set_yticklabels([f"seed {s}" for s in (42, 43, 44, 45, 46)]); ax.set_xlabel("exact tuple match (%)"); ax.set_title(title, loc="left"); ax.grid(axis="x", zorder=0); ax.set_axisbelow(True)
    axes[0].legend(handles=[Line2D([], [], marker="o", color=C["blue"], lw=0, ms=7, label="fp32"), Line2D([], [], marker="o", color=C["orange"], lw=0, ms=7, label="mixed 4/6/8-bit")], fontsize=8, loc="lower left")
    save(fig, "F08_quantization_equivalence", "fp32 vs mixed 4/6/8-bit weight quantization per seed (paired). Mean differences −0.19 pp (a) and −0.42 pp (b); both pass a ±3 pp TOST equivalence test.", rows, "backend/reports/scale_grid_vocab_natural_q4/*; scale_grid_combo_q4/*")


# F9 CPU deployment benchmark: latency (a) and file size (b), one axis each
def f9():
    order = [("prod_mixed4_23M", "deployed 23.4M, mixed-bit"), ("W384_mixed4_s42", "d384 L8 V24k, mixed-bit"), ("V4k_fp32_s42", "d384 L8 V4k, fp32"), ("V4k_mixed4_s42", "d384 L8 V4k, mixed-bit (selected)"), ("C4kL4_mixed4_s42", "d384 L4 V4k, mixed-bit")]
    d = {n: json.loads((R / "deploy_benchmark_t4" / f"{n}.json").read_text(encoding="utf-8")) for n, _ in order}
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.2))
    y = list(range(len(order)))[::-1]; labels = [l for _, l in order]
    ax = axes[0]
    for yi, (n, _) in zip(y, order):
        l = d[n]["latency_ms"]; col = C["orange"] if "selected" in dict(order)[n] else C["blue"]
        ax.plot([l["median"], l["p95"]], [yi, yi], color=col, lw=2, zorder=2); ax.scatter([l["median"]], [yi], s=50, color=col, edgecolors=C["surface"], linewidths=1.2, zorder=3); ax.scatter([l["p95"]], [yi], s=26, color=col, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8); ax.set_xlabel("CPU latency per utterance (ms): median ● to p95 •"); ax.set_xlim(0, 140); ax.set_title("(a) latency (production runtime, 4 threads)", loc="left"); ax.grid(axis="x", zorder=0); ax.set_axisbelow(True)
    ax = axes[1]
    sizes = [d[n]["checkpoint_mb"] if "fp32" not in n else d[n]["checkpoint_mb"] for n, _ in order]
    # fp32 grid checkpoint includes optimizer state; report weights-only for it
    sizes = [62.8 if n == "V4k_fp32_s42" else s for (n, _), s in zip(order, sizes)]
    cols = [C["orange"] if "selected" in l else C["blue"] for _, l in order]
    ax.barh(y, sizes, height=0.55, color=cols, zorder=2)
    for yi, s in zip(y, sizes): ax.text(s + 1.5, yi, f"{s:.1f} MB", va="center", fontsize=8, color=C["ink2"])
    ax.set_yticks(y); ax.set_yticklabels([""] * len(y)); ax.set_xlabel("model file size (MB; fp32 = weights only)"); ax.set_xlim(0, 80); ax.set_title("(b) size on disk", loc="left"); ax.grid(axis="x", zorder=0); ax.set_axisbelow(True)
    rows = [{"model": l, "file_mb": round(s, 1), "load_s": round(d[n]["load_time_s"], 2), "peak_rss_mb": round(d[n]["peak_rss_mb"]), "median_ms": round(d[n]["latency_ms"]["median"], 1), "p95_ms": round(d[n]["latency_ms"]["p95"], 1), "invalid_json_pct": round(100 * d[n]["invalid_json_rate"], 2)} for (n, l), s in zip(order, sizes)]
    save(fig, "F09_cpu_deployment", "CPU deployment benchmark through the production runtime (KV-cache decoding, 4 threads, shared workstation): (a) median and p95 latency over 300 prompts; (b) model file size. Quantization is load-time dequantized, so it changes size, not speed.", rows, "backend/reports/deploy_benchmark_t4/*.json")


# F10 Human evaluation: trial × bulb means (a), participant means (b)
def f10():
    z = zipfile.ZipFile(REPO / "documents" / "SentiLight_설문_결과정리_v3_IRBfree.xlsx"); ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    ss = ["".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml")).find("m:sheetData", ns)
    cols = [("B", "C", "D"), ("F", "G", "H"), ("J", "K", "L"), ("N", "O", "P"), ("R", "S", "T")]
    Y = {}
    for row in sheet:
        vals = {}
        for c in row.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is None: continue
            col = "".join(ch for ch in c.get("r") if ch.isalpha()); vals[col] = ss[int(v.text)] if c.get("t") == "s" else v.text
        a = vals.get("A")
        if a and a.isdigit():
            for b, trio in enumerate(cols):
                for t, cc in enumerate(trio): Y[(int(a), b, t)] = float(vals[cc])
    P = sorted({k[0] for k in Y}); bulbs = ["bulb 1 (Gemini API)", "bulb 2 (Qwen3-0.6B)", "bulb 3 (SBERT)", "bulb 4 (CompactLM fp32)", "bulb 5 (CompactLM Q4)"]
    palette = [C["blue"], C["orange"], C["aqua"], C["yellow"], C["magenta"]]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4), gridspec_kw={"width_ratios": [1, 1.1]})
    ax = axes[0]; rows = []
    for b in range(5):
        m = [st.mean(Y[(p, b, t)] for p in P) for t in range(3)]
        ax.plot([1, 2, 3], m, color=palette[b], lw=2, marker="o", ms=7, markeredgecolor=C["surface"], markeredgewidth=1.2, label=bulbs[b])
        for t in range(3): rows.append({"panel": "trial_x_bulb", "bulb": bulbs[b], "trial": t + 1, "mean_rating": round(m[t], 2)})
    ax.set_xticks([1, 2, 3]); ax.set_xlabel("trial"); ax.set_ylabel("mean rating (0–10)"); ax.set_ylim(3, 9); ax.set_title("(a) rating by trial and lighting condition (n = 20)", loc="left"); grid(ax); ax.legend(fontsize=7, loc="lower right")
    ax = axes[1]
    pm = sorted(st.mean(Y[(p, b, t)] for b in range(5) for t in range(3)) for p in P); g = st.mean(pm)
    ax.scatter(range(len(pm)), pm, s=40, color=C["blue"], edgecolors=C["surface"], linewidths=1.2, zorder=3)
    ax.axhline(g, color=C["muted"], lw=1, zorder=1); ax.text(0.2, g + 0.15, f"grand mean {g:.2f}", color=C["ink2"], fontsize=8)
    ax.axhline(5, color=C["grid"], lw=1, zorder=0)
    ax.set_xlabel("participants (anonymous, sorted by mean rating)"); ax.set_ylabel("participant mean rating (0–10)"); ax.set_ylim(2, 9.5); ax.set_xticks([]); ax.set_title("(b) between-participant spread", loc="left"); grid(ax)
    for i, v in enumerate(pm): rows.append({"panel": "participant_means_sorted", "bulb": "", "trial": "", "mean_rating": round(v, 2), "rank": i + 1})
    # variance decomposition into csv
    gmean = st.mean(Y.values()); N = len(Y)
    def mo(idx, val): return st.mean(v for k, v in Y.items() if k[idx] == val)
    ssp = 15 * sum((mo(0, p) - gmean) ** 2 for p in P); ssb = 60 * sum((mo(1, b) - gmean) ** 2 for b in range(5)); sst_ = 100 * sum((mo(2, t) - gmean) ** 2 for t in range(3)); tot = sum((v - gmean) ** 2 for v in Y.values())
    for k, v in (("participant", ssp), ("bulb", ssb), ("trial", sst_), ("residual", tot - ssp - ssb - sst_)): rows.append({"panel": "variance_share", "bulb": k, "trial": "", "mean_rating": round(100 * v / tot, 1)})
    save(fig, "F10_human_evaluation", "Exploratory anonymous human evaluation on the physical five-bulb path (20 participants × 5 conditions × 3 trials; trial order not counterbalanced, bulb–model mapping fixed, utterance–output pairs not retained): (a) mean rating by trial for each lighting condition; (b) participant mean ratings. Variance shares: participant 34.3 %, trial 28.5 %, condition 1.6 %, residual 35.6 %.", rows, "documents/SentiLight_설문_결과정리_v3_IRBfree.xlsx (anonymous ratings only)")


# F11 Error decomposition by input structure: selected vs deployed configuration
def f11():
    d = json.loads((R / "scale_grid_combo" / "error_decomposition.json").read_text(encoding="utf-8"))["By input structure"]
    groups = ["colour + emotion + intensity", "colour + emotion", "colour + no-emotion + intensity", "colour + no-emotion", "no-colour + emotion + intensity", "no-colour + emotion", "no-colour + no-emotion + intensity", "no-colour + no-emotion"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    y = list(range(len(groups)))[::-1]; h = 0.36
    for off, key, col, lab in ((+h / 2, "W384", C["blue"], "deployed cfg d384 L8 V24k"), (-h / 2, "V2V4k", C["orange"], "selected d384 L8 V4k")):
        vals = [d[g][key]["exact"] for g in groups]; ax.barh([yy + off for yy in y], vals, height=h, color=col, label=lab, zorder=2)
    ax.set_yticks(y); ax.set_yticklabels([f"{g}  (n={d[g]['W384']['n'] // 3}/seed)" for g in groups], fontsize=8); ax.set_xlabel("exact tuple match (%)"); ax.set_xlim(0, 100); ax.grid(axis="x", zorder=0); ax.set_axisbelow(True); ax.legend(fontsize=8, loc="lower right")
    rows = [{"input_structure": g, "rows_per_seed": d[g]["W384"]["n"] // 3, "deployed_exact": round(d[g]["W384"]["exact"], 1), "selected_exact": round(d[g]["V2V4k"]["exact"], 1)} for g in groups]
    save(fig, "F11_error_by_input_structure", "Exact tuple match by input structure (test rows grouped by whether the utterance names a colour, an emotion, and a non-neutral intensity), deployed configuration vs selected model, pooled over three seeds. Inputs that omit colour or intensity are hardest for both.", rows, "backend/reports/scale_grid_combo/error_decomposition.json")


def readme():
    lines = ["# Figures for the SentiLight capacity-search paper", "", "Generated by `make_figures.py` from the analysis files in `Implement_New_Android_v6/backend/reports/`. Each figure ships as PNG (300 dpi) and PDF, with the plotted numbers in `data/<name>.csv`. Only final results are plotted (five seeds where available; three-seed cells drawn hollow).", "",
             "| Figure | Caption | Source |", "|---|---|---|"]
    for n, cap, src in FIGS: lines.append(f"| {n} | {cap} | {src} |")
    lines += ["", "Palette: validated categorical order blue / orange / aqua / yellow / magenta; ordered K_eff levels on a single-hue blue ramp. No dual axes; separate panels for measures with different units.", ""]
    lines.insert(1, "Error bars and ± values are mean ± sample SD (n − 1) across independent training seeds; open markers are individual seeds; seed counts are stated in each caption.\n")
    (HERE / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    for f in (f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11):
        try:
            f()
        except Exception as e:  # noqa: BLE001
            print("FAILED", f.__name__, repr(e)); raise
    readme(); print("done", len(FIGS), "figures")
