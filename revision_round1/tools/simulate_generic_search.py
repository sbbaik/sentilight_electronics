# -*- coding: utf-8 -*-
"""What would a generic width search, run without the enumeration-informed starting region, have cost and chosen?
(Reviewer 2, point 1: "no counterfactual search without enumeration is provided").

A prospective search cannot be re-run, but the completed grids let us replay standard search procedures exactly as a
practitioner without K_eff would have run them, charging every fine-tuning run they would have launched and stopping
where their rule stops. Replayed on both tokenizer series (24k: d ∈ {128,192,224,256,320,384,512}; 4k: {224,256,
320,384}) with the paper's own adoption rule (a step is adopted only if the gain is reliable: here, all seeds of the
cell agree in sign on the paired difference and the mean gain exceeds the pooled seed SD):

  doubling   start at the smallest width, test the next width up; stop at the first step that is not adopted.
  halving    successive halving: run every width with 1 seed, keep the top half, add a seed, keep the top half, ...
  full grid  every width with every seed (what the paper actually did)
  region     the enumeration-informed region d ∈ [256, 384] with every seed (the paper's §3.3 starting region)

Runs are counted from the grid's recorded seeds; where a procedure needs a seed the grid does not have, the cell is
treated as unavailable (reported). Numbers come from tables T03 and T08 unchanged.
"""
from __future__ import annotations

import csv
import json
import re
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "analysis/search_counterfactual"
REGION = (256, 384)


def pm(s):
    m = re.match(r"\s*([\d.]+)\s*±\s*([\d.]+)", s); return float(m.group(1)), float(m.group(2))


def load_24k():
    g = {}
    for r in csv.DictReader((HERE / "data/tables/T03_width_series_24k.csv").open(encoding="utf-8")):
        acc, sd = pm(r["exact tuple %"]); per = [float(x) for x in r["per-seed exact %"].split(",")] if r.get("per-seed exact %") else None
        g[int(r["d"])] = {"mean": acc, "sd": sd, "seeds": int(r["seeds"]), "per_seed": per}
    return g


def load_4k():
    g = {}
    for r in csv.DictReader((HERE / "data/tables/T08_width_by_tokenizer_5seeds.csv").open(encoding="utf-8")):
        if r["tokenizer"].startswith("4k"):
            acc, sd = pm(r["exact tuple %"]); per = [float(x) for x in r["per-seed exact %"].split(",")]
            g[int(r["d"])] = {"mean": acc, "sd": sd, "seeds": int(r["seeds"]), "per_seed": per}
    return g


def adopted(a, b):
    """Is the step a -> b adopted? All common seeds agree in sign and the mean gain exceeds the pooled SD."""
    if a["per_seed"] and b["per_seed"]:
        n = min(len(a["per_seed"]), len(b["per_seed"]))
        d = [b["per_seed"][i] - a["per_seed"][i] for i in range(n)]
        return all(x > 0 for x in d) and st.mean(d) > st.pstdev(d) if n > 1 else d[0] > 0
    gain = b["mean"] - a["mean"]
    return gain > max(a["sd"], b["sd"])


def doubling(grid):
    ws = sorted(grid); runs = grid[ws[0]]["seeds"]; cur = ws[0]; path = [cur]
    for nxt in ws[1:]:
        runs += grid[nxt]["seeds"]; path.append(nxt)
        if not adopted(grid[cur], grid[nxt]):
            return {"chosen": cur, "runs": runs, "path": path, "stopped_at": nxt}
        cur = nxt
    return {"chosen": cur, "runs": runs, "path": path, "stopped_at": None}


def halving(grid):
    ws = sorted(grid); alive = ws[:]; runs = 0; seeds_used = 0; rounds = []
    while len(alive) > 1:
        seeds_used += 1
        usable = [w for w in alive if grid[w]["seeds"] >= seeds_used]
        runs += len(usable)
        score = {w: st.mean(grid[w]["per_seed"][:seeds_used]) if grid[w]["per_seed"] else grid[w]["mean"] for w in usable}
        keep = sorted(usable, key=lambda w: -score[w])[: max(1, len(usable) // 2)]
        rounds.append({"seeds": seeds_used, "candidates": usable, "kept": keep})
        alive = keep
    return {"chosen": alive[0], "runs": runs, "rounds": rounds}


def main():
    out = {"region": list(REGION), "rule": "step adopted only if all common seeds agree in sign and the mean gain exceeds the seed SD of the differences", "series": {}}
    for name, grid, sel in (("24k production tokenizer", load_24k(), 384), ("4k natural tokenizer", load_4k(), 384)):
        full = sum(v["seeds"] for v in grid.values())
        region = sum(v["seeds"] for w, v in grid.items() if REGION[0] <= w <= REGION[1])
        best_full = max(grid, key=lambda w: grid[w]["mean"]); best_region = max((w for w in grid if REGION[0] <= w <= REGION[1]), key=lambda w: grid[w]["mean"])
        out["series"][name] = {"grid": {str(w): {"mean": v["mean"], "seeds": v["seeds"]} for w, v in sorted(grid.items())},
                               "full_grid": {"chosen_argmax": best_full, "runs": full},
                               "region": {"chosen_argmax": best_region, "runs": region},
                               "doubling": doubling(grid), "successive_halving": halving(grid), "paper_selected": sel}
        s = out["series"][name]
        print(f"  {name}: full grid argmax d={best_full} ({full} runs) | region argmax d={best_region} ({region} runs) | "
              f"doubling → d={s['doubling']['chosen']} ({s['doubling']['runs']} runs, stopped at {s['doubling']['stopped_at']}) | "
              f"halving → d={s['successive_halving']['chosen']} ({s['successive_halving']['runs']} runs) | selected {sel}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "generic_search_replay.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    md = ["# Generic width-search procedures replayed on the completed grids", "", f"Rule: {out['rule']}.", "",
          "| series | full grid (runs → argmax) | region [256, 384] (runs → argmax) | doubling (runs → chosen, stop) | successive halving (runs → chosen) | adopted in paper |", "|---|---|---|---|---|---|"]
    for name, s in out["series"].items():
        md.append(f"| {name} | {s['full_grid']['runs']} → d = {s['full_grid']['chosen_argmax']} | {s['region']['runs']} → d = {s['region']['chosen_argmax']} | "
                  f"{s['doubling']['runs']} → d = {s['doubling']['chosen']} (stopped at {s['doubling']['stopped_at']}) | {s['successive_halving']['runs']} → d = {s['successive_halving']['chosen']} | d = {s['paper_selected']} |")
    (OUT / "generic_search_replay.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("  written", OUT / "generic_search_replay.md")


if __name__ == "__main__":
    main()
