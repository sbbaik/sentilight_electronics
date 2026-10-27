# -*- coding: utf-8 -*-
"""Aggregate the audited-request evaluation (Reviewer 1 point 3, Reviewer 2 point 4, Reviewer 3 point 1).

The audited request set is 240 Korean requests, one per production-policy cell: 120 plain requests and 40 each
with a negated intensity, altered word order or a leading context clause. Sentences were drafted by an external
language model (GPT-6 Astra, 21 October 2026) and then read, corrected and annotated by the first author; the
policy gold for each cell is the catalogue tuple. It is NOT a sample of spontaneous user language, and every
interval below is conditional on one draft generator and one auditor.

Inputs: data/audited_requests/audited_requests_K240.jsonl and analysis/audited_eval/per_row/*.jsonl, produced by
tools/run_audited_eval.sh from the released checkpoints. The catalogue gate is replayed exactly as in the
released tools/measure_policy_gate.py. Outputs: analysis/audited_requests_eval.{json,md} and
figures/F_audited_set.png.
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import statistics as st
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parents[1]
SET = HERE / "data/audited_requests/audited_requests_K240.jsonl"
PER_ROW = HERE / "analysis/audited_eval/per_row"
OUT_JSON = HERE / "analysis/audited_requests_eval.json"
OUT_MD = HERE / "analysis/audited_requests_eval.md"
OUT_FIG = HERE / "figures/F_audited_set.png"
sys.path.insert(0, str(HERE / "code/backend"))
from common.lighting_schema import LightingValues          # noqa: E402
from common.policy_catalogue import get_catalogue          # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")
FAMILIES = {                                   # label -> (file stem, printed name)
    "selected_fp32": ("selected_V4k_L8_s", "Selected generative decoder, fp32 (15.7 M)"),
    "selected_mixed": ("selected_V4k_L8_mixed4_s", "Selected generative decoder, mixed 4/6/8-bit"),
    "reference_24k": ("deployed_W384_L8_V24k_s", "Retrained deployed architecture (23.4 M, 24k tokenizer)"),
    "head240": ("head240_s", "Size-matched 240-class head (15.8 M)"),
}
# the paper's figures for the other three distributions (Table 4 of the manuscript), for the comparison figure
PAPER = {"selected_fp32": {"development": 86.5, "unseen frames": 58.7, "stress": 7.9},
         "reference_24k": {"development": 80.8, "unseen frames": 57.4, "stress": 6.6},
         "head240": {"development": 87.2, "unseen frames": 58.3, "stress": 10.3}}
PAPER_SD = {"selected_fp32": {"development": 1.8, "unseen frames": 1.7, "stress": 0.6},
            "reference_24k": {"development": 3.6, "unseen frames": 2.4, "stress": 0.3},
            "head240": {"development": 0.7, "unseen frames": 2.3, "stress": 0.6}}
T90 = {2: 6.314, 3: 2.920, 4: 2.353, 5: 2.132}
T95 = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}
SOURCES = ("plain", "negation", "word_order", "context_clause")


def key(o):
    return tuple(int(o[d]) for d in DIMS) if o else None


def ms(xs):
    return (st.mean(xs), st.stdev(xs) if len(xs) > 1 else 0.0)


def ci(xs, table=T90):
    m, sd = ms(xs)
    if len(xs) < 2:
        return [m, m]
    h = table[len(xs)] * sd / math.sqrt(len(xs))
    return [round(m - h, 2), round(m + h, 2)]


def stat(xs):
    m, sd = ms(xs)
    return {"mean": round(m, 2), "sd": round(sd, 2), "ci90": ci(xs), "per_seed": [round(x, 2) for x in xs], "seeds": len(xs)}


def load_set():
    rows = [json.loads(l) for l in SET.open(encoding="utf-8")]
    for i, r in enumerate(rows):
        r["idx"] = i
        r["variation"] = r["source"].replace("audited_request_", "")
        r["colour_named"] = bool(r.get("base_color"))
        r["emotion_named"] = bool(r.get("emotion"))
        r["omission"] = {(True, True): "colour and emotion named", (False, True): "colour omitted",
                         (True, False): "emotion omitted", (False, False): "both omitted"}[(r["colour_named"], r["emotion_named"])]
        r["length"] = len(r["input"])
    return rows


def load_family(stem):
    """{seed: [per-row records in set order]}; rows are matched on input text, which is unique in the set."""
    out = {}
    for f in sorted(PER_ROW.glob(f"{stem}*.jsonl")):
        seed = int(f.stem.rsplit("s", 1)[1])
        recs = [json.loads(l) for l in f.open(encoding="utf-8")]
        out[seed] = recs
    return out


def main():
    cat = get_catalogue()
    aset = load_set()
    by_input = {r["input"]: r for r in aset}
    assert len(by_input) == 240, "inputs are not unique"
    # cell attributes for every catalogue tuple: the set has one row per cell, so its gold tuples give the map
    tuple_attrs = {key(r["output"]): (r.get("base_color") or "none", r.get("emotion") or "none", r.get("intensity") or "neutral") for r in aset}
    assert len(tuple_attrs) == 240

    sha = hashlib.sha256(SET.read_bytes()).hexdigest()
    result = {"set": {"rows": 240, "sha256": sha, "file": str(SET.relative_to(HERE)),
                      "by_variation": dict(collections.Counter(r["variation"] for r in aset)),
                      "mean_length_chars": {v: round(st.mean(r["length"] for r in aset if r["variation"] == v), 1) for v in SOURCES},
                      "drafting": "GPT-6 Astra (OpenAI), called 21 October 2026, one sentence per cell under a fixed brief",
                      "audit": "every sentence read, corrected where needed and annotated by the first author; policy gold = catalogue tuple of the cell",
                      "interpretation": "constructed set; intervals are conditional on one draft generator and one auditor"},
              "gate_catalogue": {"count": len(cat), "sha256": cat.sha256},
              "families": {}, "paired": {}, "selected_breakdown": {}}

    fam_rows = {}         # label -> {seed: {idx: record}}
    for label, (stem, name) in FAMILIES.items():
        fam = load_family(stem)
        if not fam:
            print(f"  [missing] {label}: no per-row files yet"); continue
        if any(len(v) < 240 for v in fam.values()) or len(fam) < 5:
            print(f"  [partial] {label}: {[len(v) for v in fam.values()]} rows per seed; skipped"); continue
        seeds = sorted(fam)
        per = {}
        for s in seeds:
            d = {}
            for rec in fam[s]:
                r = by_input[rec["input"]]
                rec["_correct"] = key(rec.get("predicted")) == key(rec["reference"])
                assert key(rec["reference"]) == key(r["output"]), "reference tuple differs from the set's gold"
                d[r["idx"]] = rec
            assert len(d) == 240, (label, s, len(d))
            per[s] = d
        fam_rows[label] = per
        exact = [100 * st.mean(per[s][i]["_correct"] for i in range(240)) for s in seeds]
        coarse = [100 * st.mean(bool(per[s][i].get("coarse")) for i in range(240)) for s in seeds]
        valid = [100 * st.mean(per[s][i].get("predicted") is not None for i in range(240)) for s in seeds]
        # gate replay, exactly as tools/measure_policy_gate.py
        rej, fr, caught, missed = [], 0, [], []
        for s in seeds:
            r_rej = r_wrong = r_caught = 0
            for i in range(240):
                rec = per[s][i]; pred = rec.get("predicted"); correct = rec["_correct"]
                if pred is None:
                    blocked = True
                else:
                    blocked = cat.gate(LightingValues(**{k: int(pred[k]) for k in DIMS}), "reject").executed is None
                r_rej += blocked; r_wrong += (not correct); r_caught += (blocked and not correct)
                if blocked and correct:
                    fr += 1
            rej.append(100 * r_rej / 240); caught.append(100 * r_caught / r_wrong if r_wrong else float("nan"))
            missed.append(100 * (r_wrong - r_caught) / 240)
        result["families"][label] = {
            "name": name, "seeds": seeds, "exact": stat(exact), "coarse": stat(coarse), "valid_output_pct": stat(valid),
            "gate": {"withheld_pct": [round(x, 2) for x in ms(rej)], "correct_answers_withheld": fr,
                     "wrong_answers_withheld_pct_of_wrong": [round(x, 2) for x in ms(caught)],
                     "wrong_answers_passed_pct_of_all": [round(x, 2) for x in ms(missed)]},
            "by_variation": {v: stat([100 * st.mean(per[s][r["idx"]]["_correct"] for r in aset if r["variation"] == v) for s in seeds]) for v in SOURCES},
        }
        print(f"  {label}: exact {result['families'][label]['exact']['mean']} ± {result['families'][label]['exact']['sd']}  "
              f"coarse {result['families'][label]['coarse']['mean']}  gate withheld {result['families'][label]['gate']['withheld_pct'][0]}%")

    # paired seed contrasts
    def paired(a, b, name):
        if a not in fam_rows or b not in fam_rows:
            return
        seeds = sorted(set(fam_rows[a]) & set(fam_rows[b]))
        diffs = [result["families"][a]["exact"]["per_seed"][result["families"][a]["seeds"].index(s)]
                 - result["families"][b]["exact"]["per_seed"][result["families"][b]["seeds"].index(s)] for s in seeds]
        result["paired"][name] = {"seeds": seeds, "diff_pp": [round(x, 2) for x in diffs], "mean": round(st.mean(diffs), 2),
                                  "ci90": ci(diffs), "ci95": ci(diffs, T95),
                                  "seeds_positive": sum(x > 0 for x in diffs), "seeds_negative": sum(x < 0 for x in diffs)}
    paired("head240", "selected_fp32", "head_minus_decoder")
    paired("selected_mixed", "selected_fp32", "mixed_minus_fp32")
    paired("selected_fp32", "reference_24k", "selected_minus_reference")

    # selected-model breakdowns on the six axes the reviewer named
    if "selected_fp32" in fam_rows:
        per = fam_rows["selected_fp32"]; seeds = sorted(per)

        def group(pred, label_of):
            groups = collections.defaultdict(list)
            for r in aset:
                if pred(r):
                    groups[label_of(r)].append(r["idx"])
            return {g: {**stat([100 * st.mean(per[s][i]["_correct"] for i in idx) for s in seeds]), "rows": len(idx)}
                    for g, idx in sorted(groups.items(), key=lambda kv: -len(kv[1]))}
        sb = result["selected_breakdown"]
        sb["by_variation"] = group(lambda r: True, lambda r: r["variation"])
        sb["colour"] = {"named vs omitted": group(lambda r: True, lambda r: "named" if r["colour_named"] else "omitted"),
                        "by_value": group(lambda r: True, lambda r: r.get("base_color") or "none")}
        sb["emotion"] = {"named vs omitted": group(lambda r: True, lambda r: "named" if r["emotion_named"] else "omitted"),
                         "by_value": group(lambda r: True, lambda r: r.get("emotion") or "none")}
        sb["intensity"] = {"by_value": group(lambda r: True, lambda r: r.get("intensity") or "neutral"),
                           "neutral vs non-neutral": group(lambda r: True, lambda r: "neutral" if (r.get("intensity") or "neutral") == "neutral" else "non-neutral")}
        sb["omission"] = group(lambda r: True, lambda r: r["omission"])
        neg_int = {r["intensity"] for r in aset if r["variation"] == "negation"}
        sb["negation_vs_plain_same_intensity"] = {
            "intensities_in_negation_rows": sorted(neg_int),
            "negation": group(lambda r: r["variation"] == "negation", lambda r: "negation (40)")["negation (40)"],
            "plain, same intensities": group(lambda r: r["variation"] == "plain" and r["intensity"] in neg_int, lambda r: "plain")["plain"]}
        sb["word_order_vs_plain"] = {"word_order": sb["by_variation"]["word_order"], "plain": sb["by_variation"]["plain"]}
        sb["context_clause_vs_plain"] = {"context_clause": sb["by_variation"]["context_clause"], "plain": sb["by_variation"]["plain"]}
        q = np.quantile([r["length"] for r in aset], [1 / 3, 2 / 3])
        sb["length_tertile_chars"] = {"cuts": [round(float(x), 1) for x in q],
                                      **group(lambda r: True, lambda r: "short" if r["length"] <= q[0] else ("medium" if r["length"] <= q[1] else "long"))}
        # which attribute a wrong tuple got wrong (only if the catalogue carries cell attributes)
        if tuple_attrs:
            wrong = collections.Counter(); n_wrong = 0
            for s in seeds:
                for r in aset:
                    rec = per[s][r["idx"]]
                    if rec["_correct"]:
                        continue
                    n_wrong += 1
                    attrs = tuple_attrs.get(key(rec.get("predicted")))
                    gold = (r.get("base_color") or "none", r.get("emotion") or "none", r.get("intensity") or "neutral")
                    if attrs is None:
                        wrong["out_of_catalogue"] += 1; continue
                    for name, a, g in zip(("colour", "emotion", "intensity"), attrs, gold):
                        wrong[name] += (a != g)
            sb["attribute_wrong_among_wrong_outputs_pct"] = {k: round(100 * v / n_wrong, 1) for k, v in wrong.items()} | {"wrong_outputs_over_seeds": n_wrong}
        # audited notes: rows the auditor corrected or annotated
        noted = [r for r in aset if r.get("audit_note")]
        sb["rows_with_audit_note"] = {"rows": len(noted),
                                      "exact": stat([100 * st.mean(per[s][r["idx"]]["_correct"] for r in noted) for s in seeds]) if noted else None}

    OUT_JSON.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---------------- markdown
    md = ["# Audited request set: evaluation summary", "",
          f"240 rows (sha256 {sha[:16]}…); {result['set']['by_variation']}; mean length (chars) {result['set']['mean_length_chars']}.",
          f"Drafting: {result['set']['drafting']}. Audit: {result['set']['audit']}.", "",
          "## Families (five seeds unless stated)", "", "| model | exact % | 90% t CI | coarse % | valid output % | gate withheld % | correct withheld | wrong withheld (% of wrong) | wrong passed (% of all) |",
          "|---|--:|---|--:|--:|--:|--:|--:|--:|"]
    for label, f in result["families"].items():
        g = f["gate"]
        md.append(f"| {f['name']} | {f['exact']['mean']} ± {f['exact']['sd']} | [{f['exact']['ci90'][0]}, {f['exact']['ci90'][1]}] | {f['coarse']['mean']} ± {f['coarse']['sd']} | {f['valid_output_pct']['mean']} | "
                  f"{g['withheld_pct'][0]} ± {g['withheld_pct'][1]} | {g['correct_answers_withheld']} | {g['wrong_answers_withheld_pct_of_wrong'][0]} ± {g['wrong_answers_withheld_pct_of_wrong'][1]} | {g['wrong_answers_passed_pct_of_all'][0]} ± {g['wrong_answers_passed_pct_of_all'][1]} |")
    md += ["", "## Exact % by request variation, all families", "", "| model | " + " | ".join(SOURCES) + " |", "|---|" + "--:|" * len(SOURCES)]
    for label, f in result["families"].items():
        md.append(f"| {f['name']} | " + " | ".join(f"{f['by_variation'][v]['mean']} ± {f['by_variation'][v]['sd']}" for v in SOURCES) + " |")
    md += ["", "## Paired seed contrasts (percentage points)", ""]
    for name, p in result["paired"].items():
        md.append(f"- {name}: mean {p['mean']:+.2f}, 90% CI [{p['ci90'][0]}, {p['ci90'][1]}], 95% CI [{p['ci95'][0]}, {p['ci95'][1]}], seeds +{p['seeds_positive']}/−{p['seeds_negative']}; per seed {p['diff_pp']}")
    sb = result.get("selected_breakdown", {})
    if sb:
        md += ["", "## Selected model (fp32), breakdowns", ""]

        def table(title, d):
            md.extend([f"### {title}", "", "| group | rows | exact % (5 seeds) | 90% CI |", "|---|--:|--:|---|"])
            md.extend(f"| {g} | {v['rows']} | {v['mean']} ± {v['sd']} | [{v['ci90'][0]}, {v['ci90'][1]}] |" for g, v in d.items() if isinstance(v, dict) and "rows" in v)
            md.append("")
        table("Variation", sb["by_variation"])
        table("Colour named vs omitted", sb["colour"]["named vs omitted"]); table("Colour value", sb["colour"]["by_value"])
        table("Emotion named vs omitted", sb["emotion"]["named vs omitted"]); table("Emotion value", sb["emotion"]["by_value"])
        table("Intensity value", sb["intensity"]["by_value"]); table("Intensity neutral vs non-neutral", sb["intensity"]["neutral vs non-neutral"])
        table("Omission pattern", sb["omission"])
        n = sb["negation_vs_plain_same_intensity"]
        table(f"Negation rows vs plain rows of the same intensities {n['intensities_in_negation_rows']}",
              {"negation": n["negation"], "plain, same intensities": n["plain, same intensities"]})
        table(f"Length tertiles (chars; cuts {sb['length_tertile_chars']['cuts']})", {k: v for k, v in sb["length_tertile_chars"].items() if k != "cuts"})
        if "attribute_wrong_among_wrong_outputs_pct" in sb:
            md += ["### Attribute wrong among wrong outputs (%)", "", json.dumps(sb["attribute_wrong_among_wrong_outputs_pct"]), ""]
        if sb["rows_with_audit_note"]["rows"]:
            md += [f"Rows carrying an audit note: {sb['rows_with_audit_note']['rows']}, exact {sb['rows_with_audit_note']['exact']['mean']} ± {sb['rows_with_audit_note']['exact']['sd']}", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    # ---------------- figure: (a) four distributions per model, the style of the manuscript's Figure 9;
    #                          (b) decoder and head on the audited set by request form
    fams = [l for l in ("selected_fp32", "reference_24k", "head240") if l in result["families"]]
    if fams:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=200, gridspec_kw={"width_ratios": [1.45, 1]})
        ax = axes[0]
        dists = ["Development\n(policy templates)", "Unseen frames\n(policy vocabulary)", "Audited requests\n(model-drafted, author-audited)", "Machine paraphrases\n(stress set)"]
        cols = {"selected_fp32": "#d9534f", "reference_24k": "#2f6db3", "head240": "#2a9d6f"}
        short = {"selected_fp32": "Selected generative decoder (15.7 M)", "reference_24k": "Retrained deployed architecture (23.4 M)", "head240": "Size-matched 240-class head (15.8 M)"}
        off = {"selected_fp32": (-0.13, 3.0), "reference_24k": (0.0, -6.0), "head240": (0.13, 3.0)}   # (dx, dy) of the value label
        for l in fams:
            f = result["families"][l]
            ys = [PAPER[l]["development"], PAPER[l]["unseen frames"], f["exact"]["mean"], PAPER[l]["stress"]]
            es = [PAPER_SD[l]["development"], PAPER_SD[l]["unseen frames"], f["exact"]["sd"], PAPER_SD[l]["stress"]]
            ax.errorbar(range(4), ys, yerr=es, fmt="-o", color=cols[l], ecolor=cols[l], lw=2, ms=6, capsize=3, label=short[l])
            for x, y in zip(range(4), ys):
                ax.text(x + off[l][0], y + off[l][1], f"{y:.1f}", ha="center", fontsize=7.5, color=cols[l])
        ax.set_xticks(range(4)); ax.set_xticklabels(dists, fontsize=7.8)
        ax.set_ylabel("exact tuple match (%)"); ax.set_ylim(0, 100); ax.legend(fontsize=7.5, loc="upper right", frameon=False)
        ax.set_title("(a) Four constructed input distributions", fontsize=9.5)
        ax = axes[1]
        labels = ["plain\n(120)", "negated\nintensity (40)", "altered\norder (40)", "context\nclause (40)"]
        series = [l for l in ("selected_fp32", "head240") if l in result["families"]]
        w = 0.72 / len(series)
        for k, l in enumerate(series):
            f = result["families"][l]["by_variation"]
            ys = [f[v]["mean"] for v in SOURCES]; es = [f[v]["sd"] for v in SOURCES]
            xs = np.arange(4) + (k - (len(series) - 1) / 2) * w
            ax.bar(xs, ys, w * 0.9, color=cols[l], yerr=es, capsize=2.5, ecolor="#333", label=short[l].split(" (")[0])
            for x, y, e in zip(xs, ys, es):
                ax.text(x, y + e + 1.8, f"{y:.1f}", ha="center", fontsize=6.8, color="#333")
        ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=7.8)
        ax.set_ylim(0, 100); ax.set_title("(b) Audited requests by request form", fontsize=9.5)
        ax.legend(fontsize=7.2, loc="upper right", frameon=False)
        for a in axes:
            a.grid(axis="y", alpha=0.25)
            for s_ in ("top", "right"):
                a.spines[s_].set_visible(False)
        fig.patch.set_facecolor("white"); fig.tight_layout()
        OUT_FIG.parent.mkdir(exist_ok=True); fig.savefig(OUT_FIG, facecolor="white"); plt.close(fig)
    print("  written", OUT_JSON.name, OUT_MD.name, OUT_FIG.name)


if __name__ == "__main__":
    main()
