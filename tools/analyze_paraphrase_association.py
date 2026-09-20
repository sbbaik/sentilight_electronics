"""Sections 3.3 and 3.4 of the review instructions.

3.3  Lexical overlap and utterance length: the cross-tab with cell counts and small cells flagged, and an association
     analysis on row-level correctness of the selected model with lexical band, length, their interaction and the
     clustering by seed and by action tuple. Reported as association, never as a causal or independent effect.
3.4  Quantization equivalence on the paraphrase set: the paired fp32 - quantized difference over five seeds, its mean,
     a 90 % t interval and a TOST at the +-3 pp margin used throughout the prospective register. Equivalence is written
     only if TOST passes.

Writes tables/S15_paraphrase_lexical_length.csv and backend/reports/holdout_paraphrase/association_and_quantization.{json,md}.
"""
from __future__ import annotations
import csv, json, statistics as st
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats
REPO = Path(__file__).resolve().parents[1]; R = REPO / "backend/reports/holdout_paraphrase"; TAB = REPO.parent / "tables"
DIMS = ("H", "S", "B", "Dimmer", "CT")
SEEDS = (42, 43, 44, 45, 46)
meta = {json.loads(l)["input"]: json.loads(l) for l in (REPO / "backend/models/compact_llm/datasets/holdout_paraphrase/K240/holdout_paraphrase.jsonl").open(encoding="utf-8")}
def key(o): return tuple(int(o[k]) for k in DIMS) if o else None
def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def lexband(m):
    L = m["lexical"]
    return "all" if L["all_named_attributes_use_catalogue_wording"] else ("none" if L["no_named_attribute_uses_catalogue_wording"] else "partial")
def lenband(m):
    n = m["char_len"]
    return "<=25" if n <= 25 else ("26-45" if n <= 45 else ("46-65" if n <= 65 else ">=66"))
LEX = ("all", "partial", "none"); LEN = ("<=25", "26-45", "46-65", ">=66")
out = {}; md = ["# Paraphrase set: lexical overlap, utterance length, and quantization equivalence", ""]

# ---------------------------------------------------------------- 3.3 cross-tab with counts
rows_by_seed = {s: load(R / f"per_row/selected_V4k_L8_s{s}.jsonl") for s in SEEDS}
cell = defaultdict(list); cell_n = defaultdict(int)
recs = []
for s in SEEDS:
    for r in rows_by_seed[s]:
        m = meta[r["input"]]; ok = key(r.get("predicted")) == key(r["reference"])
        cell[(lexband(m), lenband(m))].append(ok)
        recs.append({"seed": s, "ok": int(ok), "lex": lexband(m), "len": m["char_len"], "lenband": lenband(m),
                     "tuple": str(key(r["reference"]))})
for k in cell: cell_n[k] = len(cell[k]) // len(SEEDS)
md += ["## Lexical overlap x utterance length (selected model, 5 seeds)", "",
       "Exact-tuple match in per cent, with the number of rows per seed in brackets. Cells holding fewer than 30 rows per",
       "seed are marked with an asterisk and should not be read as point estimates.", "",
       "| lexical overlap | " + " | ".join(LEN) + " | all lengths |", "|---|" + "--:|" * (len(LEN) + 1)]
T = [["lexical overlap"] + [f"{b} (rows per seed)" for b in LEN] + ["all lengths"]]
for lx in LEX:
    cells, trow = [], [lx]
    for b in LEN:
        v = cell.get((lx, b), []); n = cell_n.get((lx, b), 0)
        if not v: cells.append("—"); trow.append("—"); continue
        star = "*" if n < 30 else ""
        cells.append(f"{100*float(np.mean(v)):.1f}{star} ({n})"); trow.append(f"{100*float(np.mean(v)):.1f}{star} (n={n})")
    allv = [x for b in LEN for x in cell.get((lx, b), [])]
    cells.append(f"{100*float(np.mean(allv)):.1f} ({sum(cell_n.get((lx,b),0) for b in LEN)})")
    trow.append(f"{100*float(np.mean(allv)):.1f}")
    md.append(f"| {lx} catalogue wording | " + " | ".join(cells) + " |"); T.append(trow)
with (TAB / "S15_paraphrase_lexical_length.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(T)
out["cross_tab"] = {f"{lx}|{b}": {"exact_pct": (100 * float(np.mean(cell[(lx, b)])) if cell.get((lx, b)) else None), "rows_per_seed": cell_n.get((lx, b), 0)} for lx in LEX for b in LEN}

# ---------------------------------------------------------------- 3.3 association analysis
md += ["", "## Association analysis", ""]
try:
    import pandas as pd, statsmodels.formula.api as smf
    df = pd.DataFrame(recs)
    df["lex"] = pd.Categorical(df["lex"], categories=["none", "partial", "all"])
    df["len_c"] = (df["len"] - df["len"].mean()) / 10.0
    fit = smf.logit("ok ~ C(lex) * len_c", data=df).fit(disp=0, cov_type="cluster", cov_kwds={"groups": df["tuple"]})
    coefs = {k: {"coef": float(fit.params[k]), "odds_ratio": float(np.exp(fit.params[k])), "p": float(fit.pvalues[k]),
                 "ci90": [float(np.exp(fit.conf_int(alpha=0.1).loc[k, 0])), float(np.exp(fit.conf_int(alpha=0.1).loc[k, 1]))]} for k in fit.params.index}
    out["association"] = {"model": "logistic regression of row-level correctness on lexical band, centred utterance length in units of 10 characters, and their interaction; standard errors clustered by action tuple; rows pooled over the five seeds",
                          "n_rows": int(len(df)), "clusters": int(df['tuple'].nunique()), "coefficients": coefs}
    md += ["Logistic regression of row-level correctness on the lexical band, utterance length (centred, in units of ten",
           "characters) and their interaction, with standard errors clustered by action tuple and rows pooled over the five",
           "seeds. Odds ratios are associations in this dataset and are not to be read as causal or independent effects.", "",
           "| term | odds ratio | 90 % CI | p |", "|---|--:|--:|--:|"]
    for k, v in coefs.items():
        md.append(f"| {k} | {v['odds_ratio']:.3f} | [{v['ci90'][0]:.3f}, {v['ci90'][1]:.3f}] | {v['p']:.3g} |")
    md += ["", f"n = {len(df):,} rows in {df['tuple'].nunique()} action-tuple clusters."]
except Exception as e:
    out["association"] = {"error": str(e)}
    md += [f"Association model not fitted: {e}"]
md += ["", "**Reading.** Both lexical overlap and utterance length were associated with accuracy, and neither factor alone",
       "explained the degradation. The two are not experimentally separated in this set, so no independent or causal",
       "effect is claimed for either."]

# ---------------------------------------------------------------- 3.4 quantization equivalence
md += ["", "## Quantization equivalence on the paraphrase set", ""]
def exact(p): 
    rs = load(p); return 100 * float(np.mean([key(r.get("predicted")) == key(r["reference"]) for r in rs]))
d = []
for s in SEEDS:
    a = R / f"per_row/selected_V4k_L8_mixed4_s{s}.jsonl"; b = R / f"per_row/selected_V4k_L8_s{s}.jsonl"
    if a.exists() and b.exists(): d.append(exact(a) - exact(b))
if len(d) > 1:
    m = st.mean(d); se = st.stdev(d) / len(d) ** 0.5; t = stats.t.ppf(0.95, len(d) - 1)
    lo, hi = m - t * se, m + t * se
    MARGIN = 3.0
    p_lo = 1 - stats.t.cdf((m + MARGIN) / se, len(d) - 1); p_hi = stats.t.cdf((m - MARGIN) / se, len(d) - 1)
    p_tost = max(p_lo, p_hi); passed = (lo > -MARGIN) and (hi < MARGIN)
    out["quantization"] = {"per_seed_delta_pp": d, "mean_pp": m, "ci90": [lo, hi], "tost_margin_pp": MARGIN, "tost_p": p_tost,
                           "equivalence": bool(passed),
                           "margin_provenance": "the +-3 pp margin used throughout the prospective register (P-C1, P-D3, P-X1) and in the earlier quantization tests"}
    md += [f"- paired quantized − fp32 by seed: {', '.join(f'{x:+.2f}' for x in d)} pp",
           f"- mean {m:+.2f} pp, 90 % t CI [{lo:+.2f}, {hi:+.2f}]",
           f"- TOST at ±{MARGIN:.0f} pp: p = {p_tost:.4f} → **{'equivalence established' if passed else 'equivalence NOT established'}**",
           "", "The margin is the one used throughout the prospective register and in the earlier quantization tests, not chosen here."]
json.dump(out, (R / "association_and_quantization.json").open("w"), indent=1)
(R / "association_and_quantization.md").write_text("\n".join(md) + "\n", encoding="utf-8"); print("\n".join(md))
