"""Common-test-set analysis: all K-series models evaluated on the fixed K48 test_rule (2,000 identical utterances).
Per (budget, d): exact % per policy model (mean ± SD, n seeds); row-level paired McNemar of each larger-policy model vs
the K48 model on the same seed (common seeds), Stouffer over seeds, Holm within budget; seed-level paired differences
with 90% t CI. Writes backend/reports/scale_grid_keff_common48/common48_analysis.{md,json}."""
import json, glob, re, math, statistics as st
from pathlib import Path
from statistics import NormalDist
from scipy import stats
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "backend/reports/scale_grid_keff_common48"
DIMS = ("H", "S", "B", "Dimmer", "CT"); N = NormalDist()
def load(f):
    out = {}
    for l in open(f, encoding="utf-8"):
        r = json.loads(l); p = r.get("predicted"); out[r["row_index"]] = bool(p) and all(int(p[k]) == int(r["reference"][k]) for k in DIMS)
    return out
def mcnemar(a, b):
    keys = a.keys() & b.keys(); bo = sum(1 for k in keys if b[k] and not a[k]); ao = sum(1 for k in keys if a[k] and not b[k]); n, k = bo + ao, min(bo, ao)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return (bo - ao) / len(keys) * 100, max(p, 1e-15)
def holm(p):
    order = sorted(range(len(p)), key=lambda i: p[i]); adj = [0.0] * len(p); run = 0.0
    for rank, i in enumerate(order): run = max(run, (len(p) - rank) * p[i]); adj[i] = min(1.0, run)
    return adj
rows = {}  # (cond, pol, d, seed) -> dict
for cond in ("fixed_steps", "fixed_epochs"):
    for f in glob.glob(str(R / cond / "per_row" / "*.jsonl")):
        m = re.search(r"(K\d+)_W(\d+)_s(\d+)", f); rows[(cond, m.group(1), int(m.group(2)), int(m.group(3)))] = load(f)
    if cond == "fixed_epochs":  # K240 is identical under both budgets; reuse fixed_steps files
        for (c, pol, d, s), v in list(rows.items()):
            if c == "fixed_steps" and pol == "K240": rows[("fixed_epochs", pol, d, s)] = v
out = {"levels": {}, "contrasts": []}
L = ["# K series on the common K48 test set (2,000 identical utterances)", "",
     "Every model is evaluated on the K48 policy's test_rule. Exact %, mean ± sample SD over available seeds. Contrasts: larger-policy model minus K48 model on the same seed (row-level McNemar per seed, Stouffer, Holm within budget; seed-level paired t CI).", ""]
for cond in ("fixed_steps", "fixed_epochs"):
    L += [f"## {cond}", "", "| d | policy | seeds | exact % on K48 test |", "|--:|---|--:|--:|"]
    for d in (256, 384):
        for pol in ("K48", "K240", "K480", "K960"):
            ss = sorted(s for (c, p, dd, s) in rows if c == cond and p == pol and dd == d)
            if not ss: continue
            v = [100 * sum(rows[(cond, pol, d, s)].values()) / len(rows[(cond, pol, d, s)]) for s in ss]
            out["levels"][f"{cond}/{pol}/d{d}"] = {"seeds": ss, "per_seed": v, "mean": st.mean(v), "sd": st.stdev(v) if len(v) > 1 else None}
            L.append(f"| {d} | {pol} | {len(ss)} | {st.mean(v):.1f}" + (f" ± {st.stdev(v):.1f}" if len(v) > 1 else "") + f" |")
    L += ["", "| d | contrast | common seeds | per-seed Δ pp | mean Δ | 90 % t CI | Stouffer z | Holm p | all seeds same sign |", "|--:|---|--:|---|--:|---|--:|--:|---|"]
    cs = []
    for d in (256, 384):
        for pol in ("K240", "K480", "K960"):
            common = sorted(s for (c, p, dd, s) in rows if c == cond and p == pol and dd == d and (cond, "K48", d, s) in rows)
            if len(common) < 2: continue
            deltas, zs = [], []
            for s in common:
                dl, p = mcnemar(rows[(cond, "K48", d, s)], rows[(cond, pol, d, s)]); deltas.append(dl); zs.append(-N.inv_cdf(p / 2) * (1 if dl > 0 else -1 if dl < 0 else 0))
            Z = sum(zs) / math.sqrt(len(zs)); pc = 2 * (1 - N.cdf(abs(Z))); m = st.mean(deltas); se = st.stdev(deltas) / math.sqrt(len(deltas)); t = stats.t.ppf(0.95, len(deltas) - 1)
            cs.append({"d": d, "contrast": f"{pol} − K48", "seeds": common, "deltas": deltas, "mean": m, "ci90": [m - t * se, m + t * se], "z": Z, "p": pc, "same_sign": all(x < 0 for x in deltas) or all(x > 0 for x in deltas)})
    for c, pa in zip(cs, holm([c["p"] for c in cs])): c["holm_p"] = pa
    out["contrasts"] += [{"budget": cond, **c} for c in cs]
    for c in cs:
        L.append(f"| {c['d']} | {c['contrast']} | {len(c['seeds'])} | {', '.join(f'{x:+.1f}' for x in c['deltas'])} | {c['mean']:+.1f} | [{c['ci90'][0]:+.1f}, {c['ci90'][1]:+.1f}] | {c['z']:+.1f} | {c['holm_p']:.1e} | {'✓' if c['same_sign'] else '✗'} |")
    L.append("")
(R / "common48_analysis.md").write_text("\n".join(L) + "\n", encoding="utf-8"); (R / "common48_analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("\n".join(L))
