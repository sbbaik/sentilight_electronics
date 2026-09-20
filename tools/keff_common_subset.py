"""Common-action-subset analysis for the K series (no new training).
For every K-series model (policy x width x seed, both SFT budgets) compute exact tuple match on
  (a) all rows of its own test set, (b) rows whose lattice cell lies in the K48 catalogue, (c) rows in the K240 catalogue,
  (d) rows outside K240 (new actions), and (e) macro accuracy = mean over reachable actions of per-action exact rate.
Writes backend/reports/scale_grid_keff_fs/common_subset_analysis.{md,json}."""
import json, glob, re, statistics as st
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "backend" / "reports"
pol = json.load(open(ROOT / "config" / "keff_policies.json"))["policies"]
def cells(p): return {(c, e, i) for c in [None] + list(p["colors"]) for e in [None] + list(p["emotions"]) for i in p["intensities"]}
C48, C240 = cells(pol["K48"]), cells(pol["K240"])
DIMS = ("H", "S", "B", "Dimmer", "CT")
def exact(r): p = r.get("predicted"); return bool(p) and all(int(p[k]) == int(r["reference"][k]) for k in DIMS)
def cell(r): return (r.get("base_color") or None, r.get("emotion") or None, r.get("intensity") or "neutral")
def rate(rows): return 100 * sum(exact(r) for r in rows) / len(rows) if rows else None
def macro(rows):
    by = defaultdict(list)
    for r in rows: by[tuple(int(r["reference"][k]) for k in DIMS)].append(exact(r))
    return 100 * st.mean(sum(v) / len(v) for v in by.values()), len(by)
SRC = {"fixed_steps": {"K48": R / "scale_grid_keff_fs/K48", "K240": R / "scale_grid_width", "K480": R / "scale_grid_keff_fs/K480", "K960": R / "scale_grid_keff_fs/K960"},
       "fixed_epochs": {"K48": R / "scale_grid_keff/K48", "K240": R / "scale_grid_width", "K480": R / "scale_grid_keff/K480", "K960": R / "scale_grid_keff/K960"}}
res = defaultdict(lambda: defaultdict(list))
for cond, m in SRC.items():
    for pname, root in m.items():
        for f in glob.glob(str(root / "per_row" / "compactlm_W*_f100_s*.jsonl")):
            mm = re.search(r"W(\d+)_f100_s(\d+)", f); d, s = int(mm.group(1)), int(mm.group(2))
            rows = [json.loads(l) for l in open(f, encoding="utf-8")]
            in48 = [r for r in rows if cell(r) in C48]; in240 = [r for r in rows if cell(r) in C240]; new = [r for r in rows if cell(r) not in C240]
            mac, nact = macro(rows)
            res[(cond, pname, d)]["all"].append(rate(rows)); res[(cond, pname, d)]["k48"].append(rate(in48)); res[(cond, pname, d)]["k240"].append(rate(in240))
            res[(cond, pname, d)]["new"].append(rate(new) if new else None); res[(cond, pname, d)]["macro"].append(mac); res[(cond, pname, d)]["n48"] = len(in48); res[(cond, pname, d)]["n240"] = len(in240); res[(cond, pname, d)]["nnew"] = len(new); res[(cond, pname, d)]["nact"] = nact; res[(cond, pname, d)]["nseeds"] = len(res[(cond, pname, d)]["all"])
def fmt(v):
    v = [x for x in v if x is not None]
    return f"{st.mean(v):.1f} ± {st.stdev(v):.1f}" if len(v) > 1 else (f"{v[0]:.1f}" if v else "—")
L = ["# K series: common-action-subset analysis (all available seeds, exact %)", "",
     "Each model is scored on its own 2,000-row test set, restricted to rows whose lattice cell (colour, emotion, intensity) belongs to the K48 or K240 catalogue, and on rows outside K240 (actions added by the larger policies). Macro = mean over reachable actions of the per-action exact rate. Mean ± sample SD over all available seeds (n in the JSON; five where the seed fill applied, three otherwise).", ""]
out = {}
for cond in SRC:
    L += [f"## {cond}", "", "| policy | d | seeds | all rows | K48-subset rows (n) | K240-subset rows (n) | rows outside K240 (n) | macro over actions |", "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for pname in ("K48", "K240", "K480", "K960"):
        for d in (128, 192, 256, 384, 512):
            r = res.get((cond, pname, d))
            if not r: continue
            out[f"{cond}/{pname}/d{d}"] = {k: r[k] for k in r}
            L.append(f"| {pname} | {d} | {r['nseeds']} | {fmt(r['all'])} | {fmt(r['k48'])} ({r['n48']}) | {fmt(r['k240'])} ({r['n240']}) | {fmt(r['new'])} ({r['nnew']}) | {fmt(r['macro'])} |")
    L.append("")
(R / "scale_grid_keff_fs" / "common_subset_analysis.md").write_text("\n".join(L) + "\n", encoding="utf-8")
(R / "scale_grid_keff_fs" / "common_subset_analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("\n".join(L))
