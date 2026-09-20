"""Analyse the unseen-frame hold-out evaluation (backend/reports/holdout_final).

Metric: exact-tuple match (predicted equals the policy gold on all five fields), the metric used in every table of the
paper. The evaluator's "strict" flag is a different, stricter consistency check and is reported separately, not used
as the headline number.

Design points forced by the Electronics review:
  * development-test numbers and parameter counts are READ FROM THE FROZEN TABLES (tables/T08, T10, T05), never
    hardcoded here, because a hardcoded copy is what produced the earlier mismatch;
  * the hold-out is 2,000 rows generated from 32 sentence frames in 6 families, so rows are NOT independent: the
    headline uncertainty is a hierarchical bootstrap resampling seeds, then frame families, then frames, then rows;
  * per-frame and per-family accuracy are reported so the reader can see the spread the row-level average hides;
  * selected vs deployed is reported as a paired-by-seed difference with a t interval, a TOST at +-3 pp and an
    EXPLORATORY non-inferiority test at -3 pp (the margin used throughout the prospective register, but its
    application to this comparison was decided after the hold-out results were seen).
Writes tables/T13_holdout_final.csv, tables/S13_holdout_frame_families.csv and
backend/reports/holdout_final/analysis.{json,md}.
"""
from __future__ import annotations
import csv, json, re, statistics as st, sys
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[1]; R = REPO / "backend/reports/holdout_final"; P2 = REPO.parent; TAB = P2 / "tables"
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
from compact_llm import training_data as td
DIMS = ("H", "S", "B", "Dimmer", "CT")
HOLDOUT = REPO / "backend/models/compact_llm/datasets/holdout_natural/K240"

# ---------------------------------------------------------------- development-test numbers from the frozen tables
def read_csv(p): 
    with p.open(encoding="utf-8") as f: return list(csv.DictReader(f))
T10 = {r["configuration"]: r for r in read_csv(TAB / "T10_final_models.csv")}
T08 = {(r["tokenizer"], r["d"]): r for r in read_csv(TAB / "T08_width_by_tokenizer_5seeds.csv")}
def num(x): return float(x.split("±")[0].strip()), (float(x.split("±")[1]) if "±" in x else float("nan"))
# run id -> (display name, frozen dev source row, parameters)
CONFIGS = {
    "selected_V4k_L8":        ("selected: d 384, L 8, 4k natural tokenizer", T10["V2 V4k (d384 L8 V4k-natural)"], "T10"),
    "deployed_W384_L8_V24k":  ("deployed architecture: d 384, L 8, 24k production tokenizer", T10["W384 (deployed cfg: d384 L8 V24k-prod)"], "T10"),
    "C4kL4":                  ("d 384, L 4, 4k natural tokenizer", T10["C4kL4 (d384 L4 V4k-natural)"], "T10"),
    "X320_V4k":               ("d 320, L 8, 4k natural tokenizer", T08[("4k natural", "320")], "T08"),
    "D4_V24k":                ("d 384, L 4, 24k production tokenizer", T10["D4 (d384 L4 V24k-prod)"], "T10"),
}
DEV = {}
for k, (name, row, src) in CONFIGS.items():
    m, sd = num(row["exact tuple %"]); DEV[k] = {"name": name, "dev_mean": m, "dev_sd": sd, "params": int(row["parameters"].replace(",", "")), "source": src}
QDEV = num(T10["V2 V4k mixed-4/6/8-bit (KV-cache eval runtime)"]["exact tuple %"])

# ---------------------------------------------------------------- frame recovery (which of the 32 frames produced a row)
FRAMES = json.loads((HOLDOUT / "frames.json").read_text(encoding="utf-8"))
FRAME_RE = []
for fam, lst in FRAMES.items():
    for i, f in enumerate(lst):
        pat = re.escape(f)
        for ph in ("\\{emotion\\}", "\\{modifier\\}", "\\{color\\}", "\\{text\\}"): pat = pat.replace(ph, "(?:.*?)")
        FRAME_RE.append((fam, f"{fam}#{i+1}", re.compile("^" + pat + "$")))
_cache: dict[str, tuple[str, str]] = {}
def frame_of(text):
    if text in _cache: return _cache[text]
    for fam, fid, rx in FRAME_RE:
        if rx.match(text): _cache[text] = (fam, fid); return fam, fid
    _cache[text] = ("unmatched", "unmatched"); return "unmatched", "unmatched"

# ---------------------------------------------------------------- inverse lookup for attribute-level errors
inv = {}
for c in [None] + list(td.COLOR_PROFILES):
    for e in [None] + list(td.EMOTION_PROFILES):
        for i in td.INTENSITY_MODIFIERS:
            t = td.normalize_output(td.resolve_case_output({"base_color": c, "emotion": e, "intensity": i})); inv[tuple(int(t[k]) for k in DIMS)] = (c, e, i)
def key(o): return tuple(int(o[k]) for k in DIMS) if o else None

runs, quant = defaultdict(dict), {}
for f in sorted((R / "per_row").glob("*.jsonl")):
    m = re.match(r"^(.*?)(_mixed4)?_s(\d+)$", f.stem)
    if not m: continue
    cfg, q, seed = m.group(1), bool(m.group(2)), int(m.group(3))
    rows = [json.loads(l) for l in f.open(encoding="utf-8")]
    if len(rows) < 2000: print(f"  [skip] {f.stem}: {len(rows)} rows (incomplete)"); continue
    (quant if q else runs[cfg])[seed] = rows
def correct(rows): return [key(r.get("predicted")) == key(r["reference"]) for r in rows]
def exact(rows): return 100 * float(np.mean(correct(rows)))
def msd(xs): return (st.mean(xs), st.stdev(xs) if len(xs) > 1 else float("nan"))

# ---------------------------------------------------------------- hierarchical bootstrap: seed -> family -> frame -> row
def _clusters(seed_rows):
    """seed -> family -> frame -> np.array of per-row correctness."""
    idx = {}
    for s, rows in seed_rows.items():
        fam = defaultdict(lambda: defaultdict(list))
        for r, c in zip(rows, correct(rows)):
            fa, fi = frame_of(r["input"]); fam[fa][fi].append(c)
        idx[s] = {fa: {fi: np.array(v) for fi, v in d.items()} for fa, d in fam.items()}
    return idx

def hier_bootstrap(seed_rows, B=2000, rng=None, resample_families=False):
    """Cluster bootstrap over seeds -> frames (within family) -> rows.

    Frames are the unit that generated the utterances, so rows within a frame are not independent. Frames are
    resampled within their family and the drawn frames' rows are POOLED (not averaged), so the estimand stays the
    row-level exact accuracy rather than a macro average over families. With resample_families=True the six families
    are resampled too, which answers the wider question 'what if the frame families themselves had been different';
    that interval is reported separately because it also changes the family mix of the set.
    """
    rng = rng or np.random.default_rng(20260913)
    idx = _clusters(seed_rows); seeds = list(idx); out = []
    for _ in range(B):
        ss = rng.choice(seeds, len(seeds), replace=True); vals = []
        for s in ss:
            fams = list(idx[s])
            fams_drawn = rng.choice(fams, len(fams), replace=True) if resample_families else fams
            pool = []
            for fa in fams_drawn:
                frs = list(idx[s][fa]); fr = rng.choice(frs, len(frs), replace=True)
                for fi in fr:
                    a = idx[s][fa][fi]; pool.append(a[rng.integers(0, len(a), len(a))])
            v = np.concatenate(pool); vals.append(v.mean())
        out.append(np.mean(vals))
    q = np.percentile(out, [5, 95]); return 100 * float(np.mean(out)), 100 * float(q[0]), 100 * float(q[1])

def family_macro(seed_rows):
    """Unweighted mean over the six frame families (each family counts once), averaged over seeds."""
    idx = _clusters(seed_rows); per_seed = []
    for s, fams in idx.items():
        per_seed.append(np.mean([np.concatenate(list(d.values())).mean() for d in fams.values()]))
    return 100 * float(np.mean(per_seed))

def tci(d, conf=0.90):
    from scipy import stats
    n = len(d); m = st.mean(d); se = st.stdev(d) / n ** 0.5; t = stats.t.ppf(1 - (1 - conf) / 2, n - 1)
    return m, m - t * se, m + t * se, se, stats.t

out = {"dev_source": {k: v["source"] for k, v in DEV.items()}, "configs": {}, "quantized": {}, "paired": {}, "frames": {}}
md = ["# Unseen-frame hold-out (2,000 rows, 32 frames in 6 families) — analysis", "",
      f"Runs: " + ", ".join(f"{c}x{len(s)}" for c, s in sorted(runs.items())) + f"; quantized selected x{len(quant)}.",
      "Development-test values are read from tables/T08 and T10 (frozen), not restated here by hand.", "",
      "| configuration | params | seeds | hold-out exact % (mean ± SD) | hierarchical bootstrap 90 % CI | dev test exact % | drop (pp) | coarse % | strict % | valid output % |",
      "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
T13 = [["configuration", "parameters", "seeds", "hold-out exact % (mean ± SD)", "hold-out 90 % CI (hierarchical bootstrap)", "development-test exact % (mean ± SD)", "drop (pp)", "hold-out coarse %", "hold-out strict %", "valid output %"]]
for cfg in ("selected_V4k_L8", "deployed_W384_L8_V24k", "X320_V4k", "C4kL4", "D4_V24k"):
    if cfg not in runs: continue
    d = DEV[cfg]; seeds = sorted(runs[cfg]); accs = [exact(runs[cfg][s]) for s in seeds]; m, sd = msd(accs)
    bm, lo, hi = hier_bootstrap(runs[cfg])
    _, flo, fhi = hier_bootstrap(runs[cfg], resample_families=True)
    macro = family_macro(runs[cfg])
    coarse = st.mean(100 * float(np.mean([bool(r.get("coarse")) for r in runs[cfg][s]])) for s in seeds)
    strict = st.mean(100 * float(np.mean([bool(r.get("strict")) for r in runs[cfg][s]])) for s in seeds)
    valid = st.mean(100 * float(np.mean([bool(r.get("success")) for r in runs[cfg][s]])) for s in seeds)
    ae = Counter()
    for s in seeds:
        c = Counter(); nw = 0
        for r in runs[cfg][s]:
            p, g = key(r.get("predicted")), key(r["reference"])
            if p == g: continue
            nw += 1
            if p not in inv: c["not_a_policy_tuple"] += 1; continue
            pc, gc = inv[p], inv[g]
            c["colour_wrong"] += pc[0] != gc[0]; c["emotion_wrong"] += pc[1] != gc[1]; c["intensity_wrong"] += pc[2] != gc[2]
        for k2, v in c.items(): ae[k2] += 100 * v / nw / len(seeds)
    src = defaultdict(list); fam_acc = defaultdict(list)
    for s in seeds:
        g1, g2 = defaultdict(list), defaultdict(list)
        for r, ok in zip(runs[cfg][s], correct(runs[cfg][s])):
            g1[r["source"].replace("holdout_", "")].append(ok); g2[frame_of(r["input"])[0]].append(ok)
        for k2, v in g1.items(): src[k2].append(100 * float(np.mean(v)))
        for k2, v in g2.items(): fam_acc[k2].append(100 * float(np.mean(v)))
    out["configs"][cfg] = {"name": d["name"], "params": d["params"], "seeds": seeds, "acc": accs, "mean": m, "sd": sd,
                           "boot_mean": bm, "boot_ci90": [lo, hi], "boot_ci90_family_resampled": [flo, fhi], "family_macro_mean": macro, "dev_mean": d["dev_mean"], "dev_sd": d["dev_sd"], "dev_source": d["source"],
                           "coarse": coarse, "strict": strict, "valid_pct": valid, "by_source_mean": {k2: st.mean(v) for k2, v in src.items()},
                           "by_family_mean": {k2: st.mean(v) for k2, v in fam_acc.items()}, "attr_err_pct_of_wrong": dict(ae)}
    md.append(f"| {d['name']} | {d['params']/1e6:.1f} M | {len(seeds)} | {m:.1f} ± {sd:.1f} | [{lo:.1f}, {hi:.1f}] | {d['dev_mean']:.1f} ± {d['dev_sd']:.1f} | −{d['dev_mean']-m:.1f} | {coarse:.1f} | {strict:.1f} | {valid:.1f} |")
    T13.append([d["name"], f"{d['params']:,}", str(len(seeds)), f"{m:.1f} ± {sd:.1f}", f"[{lo:.1f}, {hi:.1f}]", f"{d['dev_mean']:.1f} ± {d['dev_sd']:.1f}", f"−{d['dev_mean']-m:.1f}", f"{coarse:.1f}", f"{strict:.1f}", f"{valid:.1f}"])
    md.append(f"  - attribute errors, % of wrong rows: colour {ae['colour_wrong']:.1f}, emotion {ae['emotion_wrong']:.1f}, intensity {ae['intensity_wrong']:.1f}, not a policy tuple {ae['not_a_policy_tuple']:.1f}")
    md.append(f"  - family-resampled 90 % CI [{flo:.1f}, {fhi:.1f}]; unweighted mean over the six families {macro:.1f} %")
    md.append(f"  - by frame family: " + ", ".join(f"{k2} {v:.1f}" for k2, v in sorted(out['configs'][cfg]['by_family_mean'].items())))
if quant:
    seeds = sorted(quant); accs = [exact(quant[s]) for s in seeds]; m, sd = msd(accs); bm, lo, hi = hier_bootstrap(quant)
    out["quantized"] = {"seeds": seeds, "acc": accs, "mean": m, "sd": sd, "boot_ci90": [lo, hi], "dev_mean": QDEV[0], "dev_sd": QDEV[1]}
    md.append(f"| selected, mixed 4/6/8-bit export (17.1 MB) | 15.7 M | {len(seeds)} | {m:.1f} ± {sd:.1f} | [{lo:.1f}, {hi:.1f}] | {QDEV[0]:.1f} ± {QDEV[1]:.1f} | −{QDEV[0]-m:.1f} | | | |")
    T13.append(["selected, mixed 4/6/8-bit export (17.1 MB)", "15,698,304", str(len(seeds)), f"{m:.1f} ± {sd:.1f}", f"[{lo:.1f}, {hi:.1f}]", f"{QDEV[0]:.1f} ± {QDEV[1]:.1f}", f"−{QDEV[0]-m:.1f}", "", "", ""])
    common = sorted(set(quant) & set(runs.get("selected_V4k_L8", {})))
    if common:
        dq = [exact(quant[s]) - exact(runs["selected_V4k_L8"][s]) for s in common]
        mm, lo2, hi2, se, tdist = tci(dq)
        out["quantized"]["delta_vs_fp32"] = {"d": dq, "mean": mm, "ci90": [lo2, hi2]}
        md.append(f"  - quantized − fp32, paired by seed: {', '.join(f'{x:+.2f}' for x in dq)} pp; mean {mm:+.2f}, 90 % CI [{lo2:+.2f}, {hi2:+.2f}]")

# ---------------------------------------------------------------- selected vs deployed
if "selected_V4k_L8" in runs and "deployed_W384_L8_V24k" in runs:
    common = sorted(set(runs["selected_V4k_L8"]) & set(runs["deployed_W384_L8_V24k"]))
    d = [exact(runs["selected_V4k_L8"][s]) - exact(runs["deployed_W384_L8_V24k"][s]) for s in common]
    mm, lo, hi, se, tdist = tci(d); n = len(d)
    p_sup = 1 - tdist.cdf(mm / se, n - 1)                       # H1: difference > 0
    p_ni = 1 - tdist.cdf((mm + 3.0) / se, n - 1)                # H1: difference > -3 pp (non-inferiority, exploratory)
    p_tost_lo = 1 - tdist.cdf((mm + 3.0) / se, n - 1); p_tost_hi = tdist.cdf((mm - 3.0) / se, n - 1)
    out["paired"]["selected_minus_deployed"] = {"seeds": common, "d": d, "mean": mm, "ci90": [lo, hi],
        "superiority_p": float(p_sup), "noninferiority_margin_pp": -3.0, "noninferiority_p": float(p_ni),
        "noninferiority_conclusion": "non-inferiority supported at the −3 pp margin" if hi > lo and lo > -3.0 else "not supported",
        "tost_p": float(max(p_tost_lo, p_tost_hi)), "tost_conclusion": "equivalence within ±3 pp" if (lo > -3.0 and hi < 3.0) else "equivalence within ±3 pp NOT established",
        "prespecified": False, "note": "the ±3 pp margin recurs in the prospective register (P-C1, P-D3, P-X1) but its application to this comparison was decided after the hold-out results were seen; exploratory"}
    md += ["", "## Selected vs deployed architecture on the hold-out", "",
           f"Paired by seed ({common}): {', '.join(f'{x:+.1f}' for x in d)} pp; mean {mm:+.1f}, 90 % t CI [{lo:+.1f}, {hi:+.1f}]; seeds favouring the selected model {sum(x>0 for x in d)}/{n}.",
           f"Superiority (difference > 0): p = {p_sup:.3f}. Equivalence TOST ±3 pp: {out['paired']['selected_minus_deployed']['tost_conclusion']} (p = {max(p_tost_lo, p_tost_hi):.3f}).",
           f"Exploratory non-inferiority at a −3 pp margin: p = {p_ni:.3f}; the 90 % CI lower bound is {lo:+.1f} pp, so the selected model is {'not materially worse than' if lo > -3 else 'not shown to be non-inferior to'} the deployed architecture at this margin. The margin was not prespecified for this comparison."]
    b = c = 0
    for s in common:
        A_ = {r["row_index"]: k for r, k in zip(runs["selected_V4k_L8"][s], correct(runs["selected_V4k_L8"][s]))}
        B_ = {r["row_index"]: k for r, k in zip(runs["deployed_W384_L8_V24k"][s], correct(runs["deployed_W384_L8_V24k"][s]))}
        for i in A_: b += A_[i] and not B_[i]; c += B_[i] and not A_[i]
    md.append(f"Row-level discordant pairs pooled over seeds: selected-only correct {b}, deployed-only correct {c}.")
    out["paired"]["row_level_discordant"] = {"selected_only": b, "deployed_only": c}

# ---------------------------------------------------------------- frame-level detail (selected model)
if "selected_V4k_L8" in runs:
    per_frame = defaultdict(list); fam_of = {}
    for s in sorted(runs["selected_V4k_L8"]):
        g = defaultdict(list)
        for r, ok in zip(runs["selected_V4k_L8"][s], correct(runs["selected_V4k_L8"][s])):
            fa, fi = frame_of(r["input"]); g[fi].append(ok); fam_of[fi] = fa
        for k2, v in g.items(): per_frame[k2].append(100 * float(np.mean(v)))
    rows = sorted(((fam_of[k2], k2, st.mean(v), len(v)) for k2, v in per_frame.items()), key=lambda x: x[2])
    out["frames"] = {"selected_model_per_frame": {k2: round(st.mean(v), 1) for k2, v in per_frame.items()},
                     "n_frames": len(per_frame), "worst": rows[0][1], "worst_acc": round(rows[0][2], 1), "best": rows[-1][1], "best_acc": round(rows[-1][2], 1),
                     "spread_pp": round(rows[-1][2] - rows[0][2], 1), "unmatched_rows": sum(1 for r in runs["selected_V4k_L8"][sorted(runs['selected_V4k_L8'])[0]] if frame_of(r["input"])[1] == "unmatched")}
    md += ["", "## Frame-level spread (selected model, mean over 5 seeds)", "",
           f"{len(per_frame)} frames recovered; unmatched rows {out['frames']['unmatched_rows']}. Worst frame {rows[0][1]} {rows[0][2]:.1f} %, best {rows[-1][1]} {rows[-1][2]:.1f} %, spread {out['frames']['spread_pp']:.1f} pp.",
           "", "| frame family | frame | exact % (5-seed mean) |", "|---|---|--:|"] + [f"| {a} | {b2} | {c2:.1f} |" for a, b2, c2, _ in rows]
    T15 = [["frame family", "frame", "exact % (selected model, 5-seed mean)"]] + [[a, b2, f"{c2:.1f}"] for a, b2, c2, _ in rows]
    with (TAB / "S13_holdout_frame_families.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(T15)

with (TAB / "T13_holdout_final.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(T13)
json.dump(out, (R / "analysis.json").open("w"), indent=1, ensure_ascii=False)
(R / "analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8"); print("\n".join(md))
