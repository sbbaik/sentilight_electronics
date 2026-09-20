"""Ring analysis for the K series: score each model on the rows of its own test set grouped by nested ring of the
lattice cell: R48 = K48 cells, R240 = K240 \\ K48, R480 = K480 \\ K240, R960 = K960 \\ K480. Also per-series run
inventory counted from disk. Writes backend/reports/scale_grid_keff_fs/ring_analysis.{md,json} and
backend/reports/run_inventory_counts.json."""
import json, glob, re, os, statistics as st
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "backend" / "reports"
pol = json.load(open(ROOT / "config" / "keff_policies.json"))["policies"]
def cells(p): return {(c, e, i) for c in [None] + list(p["colors"]) for e in [None] + list(p["emotions"]) for i in p["intensities"]}
C = {k: cells(pol[k]) for k in ("K48", "K240", "K480", "K960")}
RING = [("R48", C["K48"]), ("R240", C["K240"] - C["K48"]), ("R480", C["K480"] - C["K240"]), ("R960", C["K960"] - C["K480"])]
DIMS = ("H", "S", "B", "Dimmer", "CT")
def exact(r): p = r.get("predicted"); return bool(p) and all(int(p[k]) == int(r["reference"][k]) for k in DIMS)
def cell(r): return (r.get("base_color") or None, r.get("emotion") or None, r.get("intensity") or "neutral")
SRC = {"fixed_steps": {"K48": R / "scale_grid_keff_fs/K48", "K240": R / "scale_grid_width", "K480": R / "scale_grid_keff_fs/K480", "K960": R / "scale_grid_keff_fs/K960"},
       "matched_exposure": {"K48": R / "scale_grid_keff/K48", "K240": R / "scale_grid_width", "K480": R / "scale_grid_keff/K480", "K960": R / "scale_grid_keff/K960"}}
res = defaultdict(lambda: defaultdict(list)); nrows = {}
for cond, m in SRC.items():
    for pname, root in m.items():
        for f in glob.glob(str(root / "per_row" / "compactlm_W*_f100_s*.jsonl")):
            d = int(re.search(r"W(\d+)_", f).group(1)); rows = [json.loads(l) for l in open(f, encoding="utf-8")]
            for rname, rc in RING:
                rr = [r for r in rows if cell(r) in rc]
                if rr: res[(cond, pname, d)][rname].append(100 * sum(exact(r) for r in rr) / len(rr)); nrows[(pname, rname)] = len(rr)
def fmt(v): return f"{st.mean(v):.1f} ± {st.stdev(v):.1f}" if len(v) > 1 else (f"{v[0]:.1f}" if v else "—")
L = ["# K series: ring analysis (exact % by nested ring of the lattice cell)", "",
     "Rings: R48 = K48 cells; R240 = K240 \\ K48; R480 = K480 \\ K240; R960 = K960 \\ K480. Each model is scored on its own policy's test rows, which share action cells but not utterances with the other policies' test sets; cross-policy ring comparisons are therefore descriptive. n rows per ring in parentheses. Mean ± sample SD over available seeds.", ""]
out = {}
for cond in SRC:
    L += [f"## {cond}", "", "| policy | d | seeds | R48 | R240 | R480 | R960 |", "|---|--:|--:|--:|--:|--:|--:|"]
    for pname in ("K48", "K240", "K480", "K960"):
        for d in (128, 192, 256, 384, 512):
            r = res.get((cond, pname, d))
            if not r: continue
            n = len(r["R48"]); out[f"{cond}/{pname}/d{d}"] = {k: v for k, v in r.items()}; out[f"{cond}/{pname}/d{d}"]["nseeds"] = n
            L.append(f"| {pname} | {d} | {n} | " + " | ".join(f"{fmt(r[rn])} ({nrows.get((pname, rn), 0)})" if r.get(rn) else "—" for rn, _ in RING) + " |")
    L.append("")
(R / "scale_grid_keff_fs" / "ring_analysis.md").write_text("\n".join(L) + "\n", encoding="utf-8"); (R / "scale_grid_keff_fs" / "ring_analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("\n".join(L))
# ---- run inventory counted from disk, per series ----
runs = ROOT / "backend/models/compact_llm"
def count_pre(root): return sum(1 for p in glob.glob(str(runs / root / "**/pretrain/compactlm_pretrain_best.pt"), recursive=True) if not os.path.islink(os.path.dirname(p)))
def count_sft(root, sub=""): return len(glob.glob(str(runs / root / sub / "**/f100/sft/finetune_summary.json"), recursive=True))
def count_eval(rep): return len(glob.glob(str(R / rep / "**/per_row/*.jsonl"), recursive=True))
inv = {"W width (24k)": (count_pre("scale_grid_runs_width"), count_sft("scale_grid_runs_width"), count_eval("scale_grid_width"), 0),
       "K K_eff, matched exposure (fixed epochs)": (0, count_sft("scale_grid_runs_keff"), count_eval("scale_grid_keff"), 0),
       "K K_eff, fixed steps": (0, count_sft("scale_grid_runs_keff_fs"), count_eval("scale_grid_keff_fs"), 0),
       "D depth (A = 3), incl. L = 3": (count_pre("scale_grid_runs_depth"), count_sft("scale_grid_runs_depth"), count_eval("scale_grid_depth") + count_eval("scale_grid_depth_l3"), 0),
       "A depth at A = 2, incl. L = 3": (0, count_sft("scale_grid_runs_depth_a2"), count_eval("scale_grid_depth_a2") + count_eval("scale_grid_depth_a2_l3"), 0),
       "V vocabulary, template corpus": (count_pre("scale_grid_runs_vocab"), count_sft("scale_grid_runs_vocab"), count_eval("scale_grid_vocab"), 0),
       "V vocabulary, natural corpus": (count_pre("scale_grid_runs_vocab_natural"), count_sft("scale_grid_runs_vocab_natural"), count_eval("scale_grid_vocab_natural"), count_eval("scale_grid_vocab_natural_q4")),
       "C combined": (count_pre("scale_grid_runs_combo"), count_sft("scale_grid_runs_combo"), count_eval("scale_grid_combo"), count_eval("scale_grid_combo_q4")),
       "B budget": (count_pre("scale_grid_runs_budget"), count_sft("scale_grid_runs_budget"), count_eval("scale_grid_budget"), 0),
       "X width under V4k": (count_pre("scale_grid_runs_width_v4k"), count_sft("scale_grid_runs_width_v4k"), count_eval("scale_grid_width_v4k"), 0),
       "K common-test-set evaluations (existing checkpoints on the K48 test)": (0, 0, count_eval("scale_grid_keff_common48"), 0)}
tot = [sum(v[i] for v in inv.values()) for i in range(4)]
json.dump({"series": {k: dict(zip(("pretrain", "sft", "eval_fp32", "eval_quant"), v)) for k, v in inv.items()}, "total": dict(zip(("pretrain", "sft", "eval_fp32", "eval_quant"), tot))}, open(R / "run_inventory_counts.json", "w"), indent=1)
print("\ninventory:", inv, "\ntotal:", tot)
