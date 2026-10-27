# -*- coding: utf-8 -*-
"""Random-subset policies with the semantic composition of the production policy held fixed (R1-1, R2-1).

The nested K series changes three things at once: action count, the semantic categories the added actions bring,
and (under fixed steps) exposure per action. Here only the action count changes: nested random subsets of the
240 production cells (48, 96, 144) keep every colour, emotion and intensity category, and their training rows
are exactly the K240 rows of the kept cells, so exposure per action is unchanged (~205 rows per cell). A model
trained on a subset is evaluated on the K240 test rows of its own cells and on the rows of the smallest subset
(the common test, whose gold is identical for every model trained on a superset).

Writes data/datasets/random_subsets/K{48,96,144}r/{train_100,val,test_rule}.jsonl, the common test, cells.json
and a manifest with hashes and composition counts. Further independent draws (--draw 2, --draw 3) use their own
recorded seed and are written under data/datasets/random_subsets/draw{n}/; draw 1 is the original series.
"""
from __future__ import annotations

import collections
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "data/datasets/K240_keff"
OUT = HERE / "data/datasets/random_subsets"
SIZES = (48, 96, 144)
SEED = 20261023
DRAW_SEEDS = {1: 20261023, 2: 20261027, 3: 20261028}


def cell(r):
    return (r.get("base_color") or "none", r.get("emotion") or "none", r.get("intensity") or "neutral")


def load(name):
    return [json.loads(l) for l in (SRC / f"{name}.jsonl").open(encoding="utf-8")]


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    global SEED, OUT
    draw = int(sys.argv[sys.argv.index("--draw") + 1]) if "--draw" in sys.argv else 1
    SEED = DRAW_SEEDS[draw]
    if draw > 1:
        OUT = OUT / f"draw{draw}"
    train, val, test = load("train_100"), load("val"), load("test_rule")
    cells = sorted({cell(r) for r in train})
    assert len(cells) == 240
    rng = random.Random(SEED)
    order = cells[:]; rng.shuffle(order)
    manifest = {**({"draw": draw} if draw > 1 else {}), "seed": SEED, "source": str(SRC.relative_to(HERE)), "policies": {}}
    for k in SIZES:
        keep = set(order[:k]); name = f"K{k}r"; d = OUT / name; d.mkdir(parents=True, exist_ok=True)
        parts = {}
        for split, rows in (("train_100", train), ("val", val), ("test_rule", test)):
            sub = [r for r in rows if cell(r) in keep]
            p = d / f"{split}.jsonl"
            with p.open("w", encoding="utf-8") as fh:
                for r in sub:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            parts[split] = {"rows": len(sub), "sha256": sha(p)}
        (d / "cells.json").write_text(json.dumps(sorted(keep), ensure_ascii=False, indent=0), encoding="utf-8")
        comp = {ax: sorted({c[i] for c in keep}) for i, ax in enumerate(("colours", "emotions", "intensities"))}
        per_cell_train = collections.Counter(cell(r) for r in train if cell(r) in keep)
        per_cell_test = collections.Counter(cell(r) for r in test if cell(r) in keep)
        manifest["policies"][name] = {"cells": k, **parts, "composition": comp,
                                      "train_rows_per_cell": {"min": min(per_cell_train.values()), "median": sorted(per_cell_train.values())[k // 2], "max": max(per_cell_train.values())},
                                      "test_rows_per_cell_min": min(per_cell_test.values()), "cells_missing_in_test": k - len(per_cell_test)}
        print(f"  {name}: train {parts['train_100']['rows']} val {parts['val']['rows']} test {parts['test_rule']['rows']}  "
              f"colours {len(comp['colours'])} emotions {len(comp['emotions'])} intensities {len(comp['intensities'])}  "
              f"train/cell {manifest['policies'][name]['train_rows_per_cell']}  test cells missing {manifest['policies'][name]['cells_missing_in_test']}")
    # common test: the K48r test rows, gold identical under every superset policy (K96r, K144r, K240)
    common = OUT / "common_test_K48r.jsonl"
    common.write_bytes((OUT / "K48r/test_rule.jsonl").read_bytes())
    manifest["common_test"] = {"file": str(common.relative_to(HERE)), "rows": sum(1 for _ in common.open(encoding="utf-8")), "sha256": sha(common)}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("  written", OUT)


if __name__ == "__main__":
    main()
