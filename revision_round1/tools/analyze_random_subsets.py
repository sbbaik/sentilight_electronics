# -*- coding: utf-8 -*-
"""E2: action count with the semantic composition held fixed (R1-1, R2-1).

Nested random subsets of the 240 production cells (K48r ⊂ K96r ⊂ K144r ⊂ K240) keep every colour, emotion and
intensity category; a subset's training rows are the K240 rows of its cells, so exposure per action is the K240
exposure. Two schedules as in the K series: matched exposure (4 epochs) and fixed steps (≈ 3,070 SFT steps for every
policy). Widths d ∈ {256, 384}, seeds 42–44, pretraining = the W-series pretraining checkpoints of the original grid (24k tokenizer; not part of the v1.0.0 record).
Every model is scored on the common K48r test (gold identical under every policy) and on its own cells' test rows.
The K240 point is the W-series checkpoint (4 epochs = both schedules).

Two further independent draws of the subsets (draw 2, draw 3; tools/build_random_subset_policies.py --draw n) were
run at d = 384 with five seeds under both schedules; each draw is scored on its own common K48r test, against the
same K240 checkpoints scored on that test. The "draws" block reports every draw separately and, per seed, the
contrast averaged over the three draws.

Writes analysis/random_subsets/random_subsets.{json,md} and figures/F_random_subsets.png.
"""
from __future__ import annotations

import csv
import glob
import json
import re
import math
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
D = HERE / "analysis/random_subsets"
DIMS = ("H", "S", "B", "Dimmer", "CT")
POL = [("K48r", 48), ("K96r", 96), ("K144r", 144), ("K240", 240)]
T90 = {2: 6.314, 3: 2.920, 4: 2.353, 5: 2.132}
T95 = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}


def key(o):
    return tuple(int(o[d]) for d in DIMS) if o else None


def exact(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    return 100 * st.mean(key(r.get("predicted")) == key(r["reference"]) for r in rows), len(rows)


def stat(xs):
    m = st.mean(xs); sd = st.stdev(xs) if len(xs) > 1 else 0.0
    h = T90[len(xs)] * sd / math.sqrt(len(xs)) if len(xs) > 1 else float("nan")
    h95 = T95[len(xs)] * sd / math.sqrt(len(xs)) if len(xs) > 1 else float("nan")
    return {"mean": round(m, 1), "sd": round(sd, 1), "ci90": [round(m - h, 1), round(m + h, 1)], "ci95": [round(m - h95, 1), round(m + h95, 1)],
            "both_exclude_zero": bool(len(xs) > 1 and (m - h95 > 0 or m + h95 < 0) and (m - h > 0 or m + h < 0)), "per_seed": [round(x, 1) for x in xs], "seeds": len(xs)}


def cell(pol, sched, d, test, base=None):
    """{seed: exact} for one grid cell; K240 comes from the W-series reference files."""
    D_ = base or D
    out = {}
    if pol == "K240":
        for f in glob.glob(str(D_ / f"per_row/K240_W{d}_s*_{test}.jsonl")):
            out[int(Path(f).stem.split("_s")[1].split("_")[0])] = exact(f)[0]
    else:
        t = "own" if test == "own" else "common"
        for f in glob.glob(str(D_ / f"per_row/{pol}_{sched}_W{d}_s*_{t}.jsonl")):
            out[int(Path(f).stem.split("_s")[1].split("_")[0])] = exact(f)[0]
    return out


def main():
    res = {"design": "nested random subsets of the 240 production cells, all categories kept, K240 exposure per cell; "
                     "pretraining = W-series pretraining checkpoints of the original grid (24k tokenizer; not in the v1.0.0 record); SFT recipe unchanged",
           "fixed_steps_epochs": {"K48r": 20, "K96r": 10, "K144r": 7, "K240": 4}, "grid": {}}
    missing = []
    for sched in ("matched", "fixed"):
        for d in (256, 384):
            for test in ("common", "own"):
                for pol, k in POL:
                    if pol == "K240" and test == "own":
                        # own test of K240 = the full development test, already reported in Table T03 (24k width series)
                        t03 = {int(r["d"]): r for r in csv.DictReader((HERE / "data/tables/T03_width_series_24k.csv").open(encoding="utf-8"))}
                        m_, sd_ = (float(x) for x in re.match(r"\s*([\d.]+)\s*±\s*([\d.]+)", t03[d]["exact tuple %"]).groups())
                        res["grid"][f"{sched}|d{d}|own|K240"] = {"cells": 240, "mean": m_, "sd": sd_, "ci90": None, "per_seed": None, "seeds": int(t03[d]["seeds"]), "source": "T03"}
                        continue
                    c = cell(pol, sched, d, test)
                    if not c:
                        missing.append((sched, d, test, pol)); continue
                    res["grid"][f"{sched}|d{d}|{test}|{pol}"] = {"cells": k, **stat([c[s] for s in sorted(c)])}
    # paired seed contrasts on the common test: each subset against K240 (same seeds 42-44) and K48r against K144r
    res["paired_common"] = {}
    for sched in ("matched", "fixed"):
        for d in (256, 384):
            cells = {pol: cell(pol, sched, d, "common") for pol, _ in POL}
            for a, b in (("K48r", "K240"), ("K144r", "K240"), ("K96r", "K240"), ("K48r", "K144r")):
                seeds = sorted(set(cells[a]) & set(cells[b]))
                if len(seeds) < 2:
                    continue
                diff = [cells[a][x] - cells[b][x] for x in seeds]
                res["paired_common"][f"{sched}|d{d}|{a}-{b}"] = {**stat(diff), "seeds_positive": sum(x > 0 for x in diff), "n": len(seeds)}
    # independent draws at d = 384 (draw 1 = the series above)
    bases = {1: D, 2: D / "draw2", 3: D / "draw3"}
    if all((b / "per_row").is_dir() for b in bases.values()):
        dr = {"design": "three independent draws of the nested subsets (seeds 20261023, 20261027, 20261028), d = 384, five seeds, "
                        "each scored on its own common K48r test; K240 = the same W-series checkpoints scored on each draw's common test",
              "per_draw": {}, "averaged_over_draws": {}}
        for sched in ("matched", "fixed"):
            per = {}
            for n, b in bases.items():
                cells = {pol: cell(pol, sched, 384, "common", b) for pol, _ in POL}
                g = {pol: stat([cells[pol][x] for x in sorted(cells[pol])]) for pol, _ in POL if len(cells[pol]) == 5}
                pc = {}
                for a, bb in (("K48r", "K240"), ("K96r", "K240"), ("K144r", "K240")):
                    seeds = sorted(set(cells[a]) & set(cells[bb]))
                    if len(seeds) == 5:
                        diff = [cells[a][x] - cells[bb][x] for x in seeds]
                        pc[f"{a}-{bb}"] = {**stat(diff), "seeds_positive": sum(x > 0 for x in diff), "n": 5, "_per_seed": dict(zip(seeds, diff))}
                per[n] = {"common_rows": sum(1 for _ in open(b / "per_row/K240_W384_s42_common.jsonl", encoding="utf-8")),
                          "grid": g, "paired": pc}
            dr["per_draw"][sched] = {str(n): {**v, "paired": {k: {kk: vv for kk, vv in q.items() if kk != "_per_seed"} for k, q in v["paired"].items()}} for n, v in per.items()}
            for c in ("K48r-K240", "K96r-K240", "K144r-K240"):
                if all(c in per[n]["paired"] for n in per):
                    avg = [st.mean(per[n]["paired"][c]["_per_seed"][x] for n in per) for x in sorted(per[1]["paired"][c]["_per_seed"])]
                    means = [per[n]["paired"][c]["mean"] for n in per]
                    dr["averaged_over_draws"][f"{sched}|{c}"] = {**stat(avg), "seeds_positive": sum(x > 0 for x in avg), "n": len(avg),
                                                                 "draw_means": means, "draw_range": [min(means), max(means)],
                                                                 "draws_meeting_rule": sum(per[n]["paired"][c]["both_exclude_zero"] for n in per)}
        res["draws"] = dr
    (D / "random_subsets.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    md = ["# Random-subset policies: action count with composition fixed", "", res["design"] + ".", ""]
    for test in ("common", "own"):
        label = "common K48r test (369 rows, gold identical for every policy)" if test == "common" else "policy's own test rows"
        md += [f"## Exact % on the {label}", "",
               "| schedule | d | K48r | K96r | K144r | K240 |", "|---|--:|--:|--:|--:|--:|"]
        for sched in ("matched", "fixed"):
            for d in (256, 384):
                vals = []
                for pol, _ in POL:
                    g = res["grid"].get(f"{sched}|d{d}|{test}|{pol}")
                    vals.append(f"{g['mean']} ± {g['sd']} ({g['seeds']}s)" if g else "—")
                md.append(f"| {sched} | {d} | " + " | ".join(vals) + " |")
        md.append("")
    md += ["## Paired seed differences on the common test (percentage points, 90% and 95% t intervals, seeds favouring the smaller policy; ✓rule = both intervals exclude zero, the paper's superiority rule)", "", "| contrast | matched d256 | matched d384 | fixed d256 | fixed d384 |", "|---|--:|--:|--:|--:|"]
    for a, b in (("K48r", "K240"), ("K96r", "K240"), ("K144r", "K240"), ("K48r", "K144r")):
        row = []
        for sched in ("matched", "fixed"):
            for d in (256, 384):
                q = res["paired_common"].get(f"{sched}|d{d}|{a}-{b}")
                row.append(f"{q['mean']:+.1f} 90% [{q['ci90'][0]:+.1f}, {q['ci90'][1]:+.1f}] 95% [{q['ci95'][0]:+.1f}, {q['ci95'][1]:+.1f}] ({q['seeds_positive']}/{q['n']}){' ✓rule' if q['both_exclude_zero'] else ''}" if q else "—")
        md.append(f"| {a} − {b} | " + " | ".join(row) + " |")
    md.append("")
    if "draws" in res:
        dr = res["draws"]
        md += ["## Three independent draws at d = 384 (five seeds; each draw on its own common K48r test)", "", dr["design"] + ".", "",
               "| schedule | draw | common rows | K48r | K96r | K144r | K240 | K48r − K240 (90%; 95%; seeds) |", "|---|--:|--:|--:|--:|--:|--:|---|"]
        for sched in ("fixed", "matched"):
            for n, v in dr["per_draw"][sched].items():
                q = v["paired"].get("K48r-K240")
                md.append(f"| {sched} | {n} | {v['common_rows']} | " + " | ".join(f"{v['grid'][p]['mean']} ± {v['grid'][p]['sd']}" if p in v["grid"] else "—" for p, _ in POL)
                          + (f" | {q['mean']:+.1f} [{q['ci90'][0]:+.1f}, {q['ci90'][1]:+.1f}]; [{q['ci95'][0]:+.1f}, {q['ci95'][1]:+.1f}]; {q['seeds_positive']}/5{' ✓rule' if q['both_exclude_zero'] else ''} |" if q else " | — |"))
        md += ["", "Averaged over the three draws, per seed (paired t over five seeds):", "", "| schedule | contrast | mean | 90% | 95% | seeds | draw means | draws meeting the rule |", "|---|---|--:|---|---|--:|---|--:|"]
        for k, q in dr["averaged_over_draws"].items():
            sched, c = k.split("|")
            md.append(f"| {sched} | {c} | {q['mean']:+.1f} | [{q['ci90'][0]:+.1f}, {q['ci90'][1]:+.1f}] | [{q['ci95'][0]:+.1f}, {q['ci95'][1]:+.1f}] | {q['seeds_positive']}/{q['n']} | "
                      + ", ".join(f"{m:+.1f}" for m in q["draw_means"]) + f" | {q['draws_meeting_rule']}/3 |")
        md.append("")
    if missing:
        md += ["Missing cells: " + ", ".join("/".join(map(str, m)) for m in missing), ""]
    (D / "random_subsets.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), dpi=200, sharey=True)
    cols = {256: "#e07b39", 384: "#2f6db3"}
    for ax, sched, title in zip(axes, ("fixed", "matched"), ("Fixed step budget (≈ 3,070 SFT steps for every policy)", "Matched presentations per action (4 epochs)")):
        for d in (256, 384):
            pts = [(k, res["grid"][f"{sched}|d{d}|common|{pol}"]) for pol, k in POL if f"{sched}|d{d}|common|{pol}" in res["grid"]]
            if not pts:
                continue
            ax.errorbar([p[0] for p in pts], [p[1]["mean"] for p in pts], yerr=[p[1]["sd"] for p in pts], fmt="o-", color=cols[d], ms=4.5, lw=1.2, capsize=2.5, label=f"d = {d}")
        ax.set_xscale("log", base=2); ax.set_xticks([48, 96, 144, 240]); ax.set_xticklabels(["48", "96", "144", "240"])
        ax.set_xlabel("cells in the training policy (random subsets of K240)"); ax.set_title(title, fontsize=9.5); ax.grid(alpha=0.25, which="both")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
    axes[0].set_ylabel("exact tuple match on the common K48r test (%)"); axes[0].legend(fontsize=8, loc="lower left", title="hidden size", title_fontsize=8)
    axes[1].text(0.98, 0.04, "3 seeds per cell; error bars = sample SD\nsame categories in every policy; K240 exposure per cell", transform=axes[1].transAxes, fontsize=7.5, ha="right", color="#444")
    fig.suptitle("Same 369 utterances and identical gold under every policy: only the number of actions differs", fontsize=9.5, y=1.0)
    fig.patch.set_facecolor("white"); fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(HERE / "figures/F_random_subsets.png", facecolor="white"); plt.close(fig)
    print("  written", D / "random_subsets.md")


if __name__ == "__main__":
    main()
