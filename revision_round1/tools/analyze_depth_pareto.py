# -*- coding: utf-8 -*-
"""Latency–accuracy trade-off across depth (Reviewer 3, point 6).

Puts the depth series on one plane — development exact match against reference-decoder latency — and marks
the Pareto front, so the choice of L is visible as a trade-off rather than asserted. Numbers come from the
frozen table T05; nothing is re-measured here.
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
T05 = HERE / "data/tables/T05_depth_series.csv"
OUT = HERE / "analysis/depth_pareto"


def parse_pm(s):
    m = re.match(r"\s*([\d.]+)\s*±\s*([\d.]+)", s)
    return (float(m.group(1)), float(m.group(2))) if m else (float(s), float("nan"))


def pareto(points):
    """Indices not dominated: nobody has both lower latency and higher accuracy."""
    keep = []
    for i, (lat, acc) in enumerate(points):
        dominated = any((l2 <= lat and a2 >= acc) and (l2 < lat or a2 > acc) for j, (l2, a2) in enumerate(points) if j != i)
        if not dominated:
            keep.append(i)
    return keep


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(T05.open(encoding="utf-8")))
    series = {}
    for r in rows:
        acc, sd = parse_pm(r["exact tuple %"])
        series.setdefault(r["policy"], []).append({"L": int(r["L"]), "params": int(r["parameters"].replace(",", "")),
                                                   "seeds": int(r["seeds"]), "exact": acc, "sd": sd,
                                                   "latency_ms": float(r["latency ms"])})
    # the selected tokenizer: d = 384 at L = 4 and L = 8 under the 4k natural tokenizer (Table 2 accuracy, five seeds;
    # reference-decoder latency from the auxiliary table S20)
    t10 = {r["configuration"]: r for r in csv.DictReader((HERE / "data/tables/T10_final_models_core.csv").open(encoding="utf-8"))}
    s20 = {r["configuration"]: r for r in csv.DictReader((HERE / "data/tables/S20_final_models_auxiliary.csv").open(encoding="utf-8"))}
    k4 = []
    for cfg, L in (("C4kL4 (d384 L4 V4k-natural)", 4), ("V2 V4k (d384 L8 V4k-natural)", 8)):
        acc, sd = parse_pm(t10[cfg]["exact tuple %"]); lat = float(s20[cfg]["latency mean / p95 ms"].split("/")[0])
        k4.append({"L": L, "params": int(t10[cfg]["parameters"].replace(",", "")), "seeds": int(t10[cfg]["seeds"]), "exact": acc, "sd": sd, "latency_ms": lat})
    series["A=3, K_eff 240, 4k tokenizer (selected)"] = k4
    result = {}
    fig, ax = plt.subplots(figsize=(6.8, 4.4), dpi=200)
    colours = {"A=3, K_eff 240 (production)": "#2f6db3", "A=2, K_eff 192 (control)": "#e07b39", "A=3, K_eff 240, 4k tokenizer (selected)": "#2a9d6f"}
    for name, pts in series.items():
        pts.sort(key=lambda p: p["L"])
        front = pareto([(p["latency_ms"], p["exact"]) for p in pts])
        for i, p in enumerate(pts):
            p["pareto"] = i in front
        result[name] = pts
        c = colours.get(name, "#555")
        ax.errorbar([p["latency_ms"] for p in pts], [p["exact"] for p in pts], yerr=[p["sd"] for p in pts],
                    fmt="o-", ms=4, lw=1, color=c, ecolor=c, alpha=0.9, capsize=2, label=name)
        fp = [p for p in pts if p["pareto"]]
        ax.scatter([p["latency_ms"] for p in fp], [p["exact"] for p in fp], s=110, facecolors="none",
                   edgecolors=c, linewidths=1.8, zorder=5)
        for p in pts:
            ax.annotate(f"L={p['L']}" + ("" if p["seeds"] == 5 else " (3s)"), (p["latency_ms"], p["exact"]),
                        textcoords="offset points", xytext=(5, 5), fontsize=7.5, color=c)
    ax.set_xlabel("reference-decoder latency (ms, fp32, no KV cache)")
    ax.set_ylabel("development exact tuple match (%)")
    ax.set_title("Depth at d = 384: accuracy against latency, 24k tokenizer series and the two 4k points (circled = Pareto front)", fontsize=9.5)
    ax.grid(alpha=0.25); ax.legend(fontsize=8, loc="lower right")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.patch.set_facecolor("white"); fig.tight_layout()
    fig.savefig(OUT / "depth_pareto.png", facecolor="white"); plt.close(fig)

    (OUT / "depth_pareto.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    md = ["# Depth: accuracy–latency trade-off (from T05)", ""]
    for name, pts in result.items():
        md += [f"## {name}", "", "| L | params | seeds | exact % | latency ms | Pareto |", "|--:|--:|--:|---|--:|:-:|"]
        md += [f"| {p['L']} | {p['params']:,} | {p['seeds']} | {p['exact']} ± {p['sd']} | {p['latency_ms']:.0f} | {'●' if p['pareto'] else ''} |" for p in pts]
        md.append("")
    (OUT / "depth_pareto.md").write_text("\n".join(md), encoding="utf-8")
    for name, pts in result.items():
        print(f"  {name}: Pareto L = {[p['L'] for p in pts if p['pareto']]}")
    print("  written", OUT)


if __name__ == "__main__":
    main()
