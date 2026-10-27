# -*- coding: utf-8 -*-
"""Where mixed-bit quantization helps and where it does not (Reviewer 3, point 5).

The reviewer is right that the export does not speed up inference and that resident memory stays near 665 MB.
This table says so in one place, column by column, from the frozen CPU benchmark (T11) and the equivalence
test (S21): what the export buys (file, load time, over-the-air cost) and what it leaves unchanged (latency,
RAM, accuracy within the margin). No new measurement.
"""
import csv, json, re
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
T11 = HERE / "data/tables/T11_cpu_deployment_benchmark.csv"; S21 = HERE / "data/tables/S21_quantization_equivalence.csv"
OUT = HERE / "analysis/quant_boundary"; OUT.mkdir(parents=True, exist_ok=True)
rows = {(r["model"], r["precision"]): r for r in csv.DictReader(T11.open(encoding="utf-8"))}
fp = rows[("d384 L8 V4k (selected)", "fp32")]; mx = rows[("d384 L8 V4k (selected)", "mixed 4/6/8-bit")]
s21 = next(r for r in csv.DictReader(S21.open(encoding="utf-8")) if r["comparison"] == "selected model")
m = re.match(r"\s*([-+\d.]+) pp, 90 % CI \[([-+\d.]+), ([-+\d.]+)\]", s21["mean Δ exact and interval"])
delta, lo, hi = (float(x) for x in m.groups())
def f(k, cast=float): return cast(fp[k]), cast(mx[k])
table = [
 ("Stored file (MB)",              *f("file MB"),            "changes", f"{float(fp['file MB'])/float(mx['file MB']):.1f}× smaller: download, OTA update and flash footprint"),
 ("Load time (s)",                  *f("load s"),             "changes", "weights read from disk once; dequantised on load"),
 ("Peak resident memory (MB)",     *f("peak RSS MB"),        "unchanged in kind", "the model runs at fp32 after load, so RAM is not reduced"),
 ("Median latency (ms, 4 threads)",*f("median ms"),          "unchanged", "same arithmetic at run time"),
 ("p95 latency (ms)",              *f("p95 ms"),             "unchanged", ""),
 ("Exact match, 300-prompt subset (%)", *f("exact % (300-prompt development subset)"), "within margin",
   f"five-seed Δ {delta:+.2f} pp, 90 % CI [{lo:+.2f}, {hi:+.2f}], TOST ±3 pp pass (S21)"),
]
md = ["# Mixed 4/6/8-bit export: what it changes and what it does not (selected d384 L8 V4k)", "",
      "| quantity | fp32 | mixed-bit | effect | note |", "|---|--:|--:|---|---|"]
md += [f"| {q} | {a:g} | {b:g} | {e} | {n} |" for q, a, b, e, n in table]
md += ["", "Reading: the export is a storage-and-distribution measure. It does not lower RAM or latency on this runtime, "
       "because weights are restored to fp32 when the model is loaded; the accuracy cost is inside the prospectively "
       "fixed ±3-point margin. Where it pays is a storage-constrained or bandwidth-constrained deployment — flash budget, "
       "over-the-air updates, cold-start load — not a compute-constrained one."]
(OUT / "quant_boundary.md").write_text("\n".join(md), encoding="utf-8")
(OUT / "quant_boundary.json").write_text(json.dumps([dict(zip(("quantity","fp32","mixed","effect","note"), t)) for t in table], indent=1), encoding="utf-8")
for q, a, b, e, n in table: print(f"  {q:38s} {a:>7g} → {b:<7g} {e}")
