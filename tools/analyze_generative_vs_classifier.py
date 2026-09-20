"""Section 3.1: generative decoding against a 240-class head on the SAME backbone and the SAME pretrained checkpoints.

Compares the selected generative model (15.7 M) with the size-matched classifier (15.8 M) over seeds 42-46 on the same
rows of each evaluation set: per-seed exact differences, mean difference with a 90 % t interval, a seed -> row
hierarchical bootstrap, a per-seed McNemar test on discordant rows with Stouffer combination, coarse and attribute-level
differences, and output validity. The point is to decide whether the difference is inconclusive or real, not to restate
two point estimates.

Reads the generative per-row files from backend/reports/{holdout_final,holdout_paraphrase} and the classifier per-row
files written by tools/instrument_compactlm_classifier.py.
Writes tables/T17_generative_vs_classifier.csv and backend/reports/baselines_nongenerative/generative_vs_classifier.{json,md}.
"""
from __future__ import annotations
import csv, json, statistics as st, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats
REPO = Path(__file__).resolve().parents[1]; TAB = REPO.parent / "tables"
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
from compact_llm import training_data as td
from common.benchmark_eval import coarse_3bin_pass  # the same coarse scorer the generative evaluator uses
DIMS = ("H", "S", "B", "Dimmer", "CT")
CLF = REPO / "backend/reports/baselines_nongenerative/classifier_instrumented/per_row"
GEN = {"dev": None,
       "frame": REPO / "backend/reports/holdout_final/per_row",
       "paraphrase": REPO / "backend/reports/holdout_paraphrase/per_row"}
SEEDS = (42, 43, 44, 45, 46)
inv = {}
for c in [None] + list(td.COLOR_PROFILES):
    for e in [None] + list(td.EMOTION_PROFILES):
        for i in td.INTENSITY_MODIFIERS:
            t = td.normalize_output(td.resolve_case_output({"base_color": c, "emotion": e, "intensity": i})); inv[tuple(int(t[k]) for k in DIMS)] = (c, e, i)
def key(o): return tuple(int(o[k]) for k in DIMS) if o else None
def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def ok_map(rows): return {r["input"]: (key(r.get("predicted")) == key(r["reference"])) for r in rows}
def coarse_rate(rows):
    """Recomputed with the evaluator's own scorer so the generative and classifier rows are scored identically."""
    v = [coarse_3bin_pass(r["reference"], r["predicted"]) for r in rows if r.get("predicted")]
    return 100 * float(np.mean(v)) if v else None
def attr_err(rows):
    c = defaultdict(int); nw = 0
    for r in rows:
        p, g = key(r.get("predicted")), key(r["reference"])
        if p == g: continue
        nw += 1
        if p not in inv: c["not_a_policy_tuple"] += 1; continue
        pc, gc = inv[p], inv[g]
        c["colour"] += pc[0] != gc[0]; c["emotion"] += pc[1] != gc[1]; c["intensity"] += pc[2] != gc[2]
    return {k: 100 * v / max(nw, 1) for k, v in c.items()}, nw
def attr_acc(rows):
    """Per-attribute accuracy over all rows, from the inverse lookup of the predicted tuple."""
    c = defaultdict(int); n = 0
    for r in rows:
        p, g = key(r.get("predicted")), key(r["reference"]); n += 1
        pg = inv.get(p); gg = inv[g]
        c["colour"] += bool(pg) and pg[0] == gg[0]; c["emotion"] += bool(pg) and pg[1] == gg[1]; c["intensity"] += bool(pg) and pg[2] == gg[2]
    return {k: 100 * v / n for k, v in c.items()}
def hier_boot(pairs, B=2000, rng=None):
    """Resample seeds, then rows within a seed; returns the difference distribution (classifier - generative)."""
    rng = rng or np.random.default_rng(20260913); out = []
    arrs = [np.array([a - b for a, b in zip(cl, ge)], dtype=float) for cl, ge in pairs]
    for _ in range(B):
        vals = []
        for j in rng.integers(0, len(arrs), len(arrs)):
            a = arrs[j]; vals.append(a[rng.integers(0, len(a), len(a))].mean())
        out.append(np.mean(vals))
    q = np.percentile(out, [5, 95]); return 100 * float(np.mean(out)), 100 * float(q[0]), 100 * float(q[1])
res = {"seeds": list(SEEDS), "sets": {}}
md = ["# Generative decoding vs a 240-class head on the same backbone", "",
      "Same pretrained checkpoints, same fine-tuning rows, same five seeds, same evaluation rows. The generative model has",
      "15,698,304 parameters and the classifier 15,790,704; they differ in the output formulation and nothing else.", ""]
T17 = [["evaluation set", "seeds per model", "generative exact % (mean ± SD)", "240-class head exact % (mean ± SD)", "difference (head − generative), pp",
        "90 % t CI", "seed → row bootstrap 90 % CI", "McNemar (Stouffer z, p)", "seeds favouring the head", "generative coarse %", "head coarse %", "generative valid output %", "head valid output %"]]
for setname, gdir in GEN.items():
    if gdir is None: continue
    gname = "selected_V4k_L8"
    clf_name = {"frame": "hold", "paraphrase": "para"}[setname]
    g_seeds, c_seeds, pairs, zs, fav = [], [], [], [], 0
    coarse_g, coarse_c, attr_g, attr_c, valid_g = [], [], [], [], []
    for s in SEEDS:
        gp = gdir / f"{gname}_s{s}.jsonl"; cp = CLF / f"clf_{clf_name}_s{s}.jsonl"
        if not gp.exists() or not cp.exists(): continue
        gr, cr = load(gp), load(cp)
        gm, cm = ok_map(gr), ok_map(cr)
        common = [k for k in gm if k in cm]
        ge = [gm[k] for k in common]; cl = [cm[k] for k in common]
        g_seeds.append(100 * float(np.mean(ge))); c_seeds.append(100 * float(np.mean(cl))); pairs.append((cl, ge))
        b = sum(1 for k in common if cm[k] and not gm[k]); c_ = sum(1 for k in common if gm[k] and not cm[k])
        if b + c_ > 0:
            z = (b - c_) / (b + c_) ** 0.5; zs.append(z)
        fav += int((100 * np.mean(cl)) > (100 * np.mean(ge)))
        cg, cc = coarse_rate(gr), coarse_rate(cr)
        if cg is not None: coarse_g.append(cg)
        if cc is not None: coarse_c.append(cc)
        attr_g.append(attr_acc(gr)); attr_c.append(attr_acc(cr))
        valid_g.append(100 * float(np.mean([bool(r.get("success")) for r in gr])))
    if not pairs: continue
    d = [c - g for c, g in zip(c_seeds, g_seeds)]
    m = st.mean(d); se = st.stdev(d) / len(d) ** 0.5; t = stats.t.ppf(0.95, len(d) - 1)
    lo, hi = m - t * se, m + t * se
    bm, blo, bhi = hier_boot(pairs)
    Z = sum(zs) / len(zs) ** 0.5 if zs else float("nan"); pz = 2 * (1 - stats.norm.cdf(abs(Z))) if zs else float("nan")
    ag = {k: st.mean([a[k] for a in attr_g]) for k in ("colour", "emotion", "intensity")}
    ac = {k: st.mean([a[k] for a in attr_c]) for k in ("colour", "emotion", "intensity")}
    verdict = ("the head is higher and the interval excludes zero" if lo > 0 else
               "the generative model is higher and the interval excludes zero" if hi < 0 else "inconclusive: the interval includes zero")
    res["sets"][setname] = {"generative": {"per_seed": g_seeds, "mean": st.mean(g_seeds), "sd": st.stdev(g_seeds)},
                            "classifier": {"per_seed": c_seeds, "mean": st.mean(c_seeds), "sd": st.stdev(c_seeds)},
                            "difference_pp": {"per_seed": d, "mean": m, "ci90": [lo, hi], "bootstrap_ci90": [blo, bhi],
                                              "mcnemar_stouffer_z": Z, "mcnemar_p": pz, "seeds_favouring_head": fav, "verdict": verdict},
                            "coarse": {"generative": (st.mean(coarse_g) if coarse_g else None), "classifier": (st.mean(coarse_c) if coarse_c else None)},
                            "attribute_accuracy": {"generative": ag, "classifier": ac},
                            "valid_output_pct": {"generative": st.mean(valid_g), "classifier": 100.0}}
    T17.append([setname, str(len(d)), f"{st.mean(g_seeds):.1f} ± {st.stdev(g_seeds):.1f}", f"{st.mean(c_seeds):.1f} ± {st.stdev(c_seeds):.1f}",
                f"{m:+.1f}", f"[{lo:+.1f}, {hi:+.1f}]", f"[{blo:+.1f}, {bhi:+.1f}]", f"z = {Z:+.2f}, p = {pz:.3f}", f"{fav}/{len(d)}",
                f"{st.mean(coarse_g):.1f}", f"{st.mean(coarse_c):.1f}", f"{st.mean(valid_g):.1f}", "100.0 (by construction)"])
    md += [f"## {setname} hold-out", "",
           f"- generative {st.mean(g_seeds):.1f} ± {st.stdev(g_seeds):.1f} %, head {st.mean(c_seeds):.1f} ± {st.stdev(c_seeds):.1f} % (5 seeds each)",
           f"- per-seed difference (head − generative): {', '.join(f'{x:+.2f}' for x in d)} pp",
           f"- mean {m:+.2f} pp, 90 % t CI [{lo:+.2f}, {hi:+.2f}], seed → row bootstrap 90 % CI [{blo:+.2f}, {bhi:+.2f}]",
           f"- row-level McNemar combined over seeds: Stouffer z = {Z:+.2f}, p = {pz:.3f}; the head is higher in {fav}/{len(d)} seeds",
           f"- **{verdict}**",
           f"- coarse three-bin (recomputed with the same scorer): generative {st.mean(coarse_g):.1f} %, head {st.mean(coarse_c):.1f} %",
           f"- attribute accuracy, generative vs head: colour {ag['colour']:.1f} vs {ac['colour']:.1f}, emotion {ag['emotion']:.1f} vs {ac['emotion']:.1f}, intensity {ag['intensity']:.1f} vs {ac['intensity']:.1f}",
           f"- valid output: generative {st.mean(valid_g):.1f} %, head 100 % by construction (a 240-class head cannot emit an out-of-schema answer)", ""]
with (TAB / "T17_generative_vs_classifier.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(T17)
OUTD = REPO / "backend/reports/baselines_nongenerative"
json.dump(res, (OUTD / "generative_vs_classifier.json").open("w"), indent=1, default=lambda o: int(o) if hasattr(o, "__int__") else str(o))
(OUTD / "generative_vs_classifier.md").write_text("\n".join(md) + "\n", encoding="utf-8"); print("\n".join(md))
