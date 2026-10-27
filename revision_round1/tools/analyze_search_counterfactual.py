# -*- coding: utf-8 -*-
"""What a width search confined to the action-set-informed starting region would have chosen (Reviewer 2, point 1).

The reviewer asks for a counterfactual: a search without enumeration. The honest version available from the
records is the reverse question — had the search been confined to the region the enumeration suggested
(d ≈ 256–384), would it have reached the same width, and at what cost? Both tokenizer series are checked
against the paper's own adoption rule, and the result is reported as a post hoc reading of a completed grid,
which is all it can be.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
T03 = HERE / "data/tables/T03_width_series_24k.csv"
T08 = HERE / "data/tables/T08_width_by_tokenizer_5seeds.csv"
OUT = HERE / "analysis/search_counterfactual"
REGION = (256, 384)       # the starting region named in §3.3


def pm(s):
    m = re.match(r"\s*([\d.]+)\s*±\s*([\d.]+)", s)
    return float(m.group(1)), float(m.group(2))


def load_24k():
    rows = []
    for r in csv.DictReader(T03.open(encoding="utf-8")):
        acc, sd = pm(r["exact tuple %"])
        rows.append({"d": int(r["d"]), "seeds": int(r["seeds"]), "exact": acc, "sd": sd,
                     "params": int(r["parameters"].replace(",", ""))})
    return rows


def load_4k():
    rows = []
    for r in csv.DictReader(T08.open(encoding="utf-8")):
        if r["tokenizer"].startswith("4k"):
            acc, sd = pm(r["exact tuple %"])
            rows.append({"d": int(r["d"]), "seeds": int(r["seeds"]), "exact": acc, "sd": sd,
                         "params": int(r["parameters"].replace(",", "")),
                         "per_seed": [float(x) for x in r["per-seed exact %"].split(",")]})
    return rows


def summarise(name, grid, selected_d):
    full = sorted(grid, key=lambda r: r["d"])
    inside = [r for r in full if REGION[0] <= r["d"] <= REGION[1]]
    best_full = max(full, key=lambda r: r["exact"])
    best_in = max(inside, key=lambda r: r["exact"])
    five_full = [r for r in full if r["seeds"] == 5]
    best_full5 = max(five_full, key=lambda r: r["exact"])
    return {
        "series": name,
        "grid_widths": [r["d"] for r in full], "grid_runs": sum(r["seeds"] for r in full),
        "region_widths": [r["d"] for r in inside], "region_runs": sum(r["seeds"] for r in inside),
        "runs_saved_if_confined": sum(r["seeds"] for r in full) - sum(r["seeds"] for r in inside),
        "best_point_estimate_full_grid": {"d": best_full["d"], "exact": best_full["exact"], "seeds": best_full["seeds"]},
        "best_point_estimate_five_seed_cells": {"d": best_full5["d"], "exact": best_full5["exact"]},
        "best_point_estimate_inside_region": {"d": best_in["d"], "exact": best_in["exact"], "seeds": best_in["seeds"]},
        "selected_d": selected_d,
        "selected_inside_region": REGION[0] <= selected_d <= REGION[1],
        "cells": full,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s24 = summarise("24k production tokenizer (W series, L = 8)", load_24k(), selected_d=384)
    s4 = summarise("4k natural tokenizer (X series, L = 8)", load_4k(), selected_d=384)

    # what the paper's own adoption rule says about leaving the region upward in the 24k series
    r384 = next(r for r in s24["cells"] if r["d"] == 384); r512 = next(r for r in s24["cells"] if r["d"] == 512)
    s24["step_384_to_512"] = {"delta_pp": round(r512["exact"] - r384["exact"], 1),
                              "note": "the paper's adoption rule (Holm-corrected row-level p < 0.05 and all seeds "
                                      "agreeing in sign) was not met for this step; width above 384 was not adopted"}
    reading = (
        "Under the 24k tokenizer the full grid (7 widths, 33 runs) and the region-confined grid (3 widths, 13 runs) "
        "lead to the same adopted width: the only reliable gain lies between d = 224 and 256, inside the region, and "
        "the step to 512 was not adopted under the prospective rule. Under the 4k tokenizer the selected d = 384 is "
        "the argmax of both the full grid (4 widths, 20 runs) and the confined grid (3 widths, 15 runs). In both "
        "series the enumeration-informed region contained the width that was eventually chosen, and confining the "
        "search to it would have cost 20 fewer runs in one series and 5 in the other. This is a reading of a grid "
        "whose outcome was already known: it shows the region was not misleading, not that a practitioner could have "
        "known in advance to trust it, and the wider sweep is what established that the region was right under one "
        "tokenizer and too low under the other."
    )
    out = {"region": list(REGION), "series": [s24, s4], "reading": reading}
    (OUT / "search_counterfactual.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    md = ["# Counterfactual: a width search confined to the enumeration-informed region", "",
          f"Region: d ∈ [{REGION[0]}, {REGION[1]}] (§3.3).", ""]
    for s in (s24, s4):
        md += [f"## {s['series']}", "",
               f"- full grid: widths {s['grid_widths']}, {s['grid_runs']} fine-tuning runs",
               f"- confined grid: widths {s['region_widths']}, {s['region_runs']} runs ({s['runs_saved_if_confined']} fewer)",
               f"- best point estimate, full grid: d = {s['best_point_estimate_full_grid']['d']} ({s['best_point_estimate_full_grid']['exact']} %, {s['best_point_estimate_full_grid']['seeds']} seeds)",
               f"- best point estimate, five-seed cells: d = {s['best_point_estimate_five_seed_cells']['d']} ({s['best_point_estimate_five_seed_cells']['exact']} %)",
               f"- best point estimate inside region: d = {s['best_point_estimate_inside_region']['d']} ({s['best_point_estimate_inside_region']['exact']} %)",
               f"- selected: d = {s['selected_d']} (inside region: {s['selected_inside_region']})", ""]
        if "step_384_to_512" in s:
            md += [f"- step 384→512: {s['step_384_to_512']['delta_pp']:+.1f} pp; {s['step_384_to_512']['note']}", ""]
    md += ["## Reading", "", reading, ""]
    (OUT / "search_counterfactual.md").write_text("\n".join(md), encoding="utf-8")
    for s in (s24, s4):
        print(f"  {s['series']}: grid {s['grid_runs']} runs → region {s['region_runs']} runs; "
              f"argmax full d={s['best_point_estimate_full_grid']['d']}, inside d={s['best_point_estimate_inside_region']['d']}, selected {s['selected_d']}")
    print("  written", OUT)


if __name__ == "__main__":
    main()
