# -*- coding: utf-8 -*-
"""Why the 240-class head falls below the decoder on the audited request set although it is ahead on the stress set.

Two pieces of evidence, both from the released checkpoints without retraining:
  1. Attribute-level reading of the audited-set outputs (stored per-row files): which attribute of the predicted cell
     is wrong, how many distinct classes each model predicts, and how concentrated its predictions are, by request form.
  2. A controlled ablation on the development test: the same 2,000 requests with a neutral clause (no colour, emotion
     or intensity word) placed before or after the request (tools/run_head_ablation.sh), head and decoder, five seeds.
     The original-sentence scores are the stored evaluation outputs.
Writes analysis/head_ablation/head_reversal.{json,md} and figures/F_head_ablation.png.
"""
from __future__ import annotations

import collections
import glob
import json
import math
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
AB = HERE / "analysis/head_ablation"
DIMS = ("H", "S", "B", "Dimmer", "CT")
T90 = {2: 6.314, 3: 2.920, 4: 2.353, 5: 2.132}
VARIANTS = (("original", None), ("lead", "neutral clause before"), ("trail", "neutral clause after"), ("lead_long", "long neutral clause before"))


def key(o):
    return tuple(int(o[d]) for d in DIMS) if o else None


def seed_of(path):
    return int(Path(path).stem.rsplit("s", 1)[1])


def exact_of(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    return 100 * st.mean(key(r.get("predicted")) == key(r["reference"]) for r in rows)


def stat(xs):
    m, sd = st.mean(xs), (st.stdev(xs) if len(xs) > 1 else 0.0)
    h = T90[len(xs)] * sd / math.sqrt(len(xs)) if len(xs) > 1 else float("nan")
    return {"mean": round(m, 2), "sd": round(sd, 2), "ci90": [round(m - h, 2), round(m + h, 2)], "per_seed": [round(x, 2) for x in xs]}


def main():
    # ---- 1. audited set, attribute reading
    aset = [json.loads(l) for l in (HERE / "data/audited_requests/audited_requests_K240.jsonl").open(encoding="utf-8")]
    attr = {key(r["output"]): (r.get("base_color") or "none", r.get("emotion") or "none", r.get("intensity") or "neutral") for r in aset}
    byin = {r["input"]: r for r in aset}
    fam = {"decoder": sorted(glob.glob(str(HERE / "analysis/audited_eval/per_row/selected_V4k_L8_s4*.jsonl"))),
           "head": sorted(glob.glob(str(HERE / "analysis/audited_eval/per_row/head240_s*.jsonl")))}
    reading = {}
    for name, files in fam.items():
        reading[name] = {}
        for form in ("plain", "negation", "word_order", "context_clause", "all"):
            n = c = e = i = oc = ex = 0; dist = collections.Counter()
            for f in files:
                for l in open(f, encoding="utf-8"):
                    r = json.loads(l); a = byin[r["input"]]
                    if form != "all" and a["variation"] != form:
                        continue
                    n += 1; p = attr.get(key(r.get("predicted"))); g = (a.get("base_color") or "none", a.get("emotion") or "none", a.get("intensity") or "neutral")
                    ex += key(r.get("predicted")) == key(r["reference"])
                    if p is None:
                        oc += 1; continue
                    c += p[0] == g[0]; e += p[1] == g[1]; i += p[2] == g[2]; dist[key(r.get("predicted"))] += 1
            reading[name][form] = {"rows_x_seeds": n, "exact": round(100 * ex / n, 1), "colour_right": round(100 * c / n, 1), "emotion_right": round(100 * e / n, 1),
                                   "intensity_right": round(100 * i / n, 1), "out_of_catalogue": round(100 * oc / n, 1), "distinct_predicted_classes": len(dist),
                                   "top_class_share": round(100 * dist.most_common(1)[0][1] / max(1, sum(dist.values())), 1)}
    # head concentration on the paper's sets, for reference
    ref = {}
    for lab, pat in (("development", "data/per_row/head/clf_dev_s*.jsonl"), ("unseen_frames", "data/per_row/head/clf_hold_s*.jsonl"), ("stress", "data/per_row/head/clf_para_s*.jsonl")):
        dist = collections.Counter(); n = 0
        for f in glob.glob(str(HERE / pat)):
            for l in open(f, encoding="utf-8"):
                r = json.loads(l); n += 1; dist[key(r.get("predicted"))] += 1
        ref[lab] = {"distinct_predicted_classes": len(dist), "top_class_share": round(100 * dist.most_common(1)[0][1] / n, 1)}

    # ---- 2. clause ablation on the development test
    abl = {}
    for model in ("head", "decoder"):
        abl[model] = {}
        for var, _ in VARIANTS:
            if var == "original":
                files = sorted(glob.glob(str(HERE / ("data/per_row/head/clf_dev_s*.jsonl" if model == "head" else "data/per_row/dev_V4k/compactlm_V4k_f100_s*.jsonl"))))
            else:
                files = sorted(glob.glob(str(AB / f"per_row/{model}_{var}_s*.jsonl")))
            if len(files) != 5:
                print(f"  [missing] {model} {var}: {len(files)} files"); continue
            abl[model][var] = {"seeds": [seed_of(f) for f in files], **stat([exact_of(f) for f in files])}
        for var, _ in VARIANTS[1:]:
            if var in abl[model] and "original" in abl[model]:
                d = [b - a for a, b in zip(abl[model]["original"]["per_seed"], abl[model][var]["per_seed"])]
                abl[model][f"delta_{var}"] = {**stat(d), "seeds_negative": sum(x < 0 for x in d)}
    out = {"audited_reading": reading, "head_concentration_reference_sets": ref, "clause_ablation_dev": abl,
           "clauses": {"lead": "퇴근하고 집에 막 들어왔는데 짐 정리는 내일 하려고. ", "trail": " 그리고 내일 아침 회의 자료는 책상 위에 둘게.",
                       "lead_long": "오늘은 외근이 두 건이나 있어서 하루가 길었어. 저녁은 간단히 먹고 설거지까지 끝냈어. "}}
    (AB / "head_reversal.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    md = ["# Why the head loses on the audited set", "", "## 1. Audited set: attribute-level reading (5 seeds pooled)", "",
          "| model | form | exact % | colour right | emotion right | intensity right | out of catalogue | distinct classes | top-class share |", "|---|---|--:|--:|--:|--:|--:|--:|--:|"]
    for name in ("decoder", "head"):
        for form, v in reading[name].items():
            md.append(f"| {name} | {form} | {v['exact']} | {v['colour_right']} | {v['emotion_right']} | {v['intensity_right']} | {v['out_of_catalogue']} | {v['distinct_predicted_classes']} | {v['top_class_share']} % |")
    md += ["", "Head prediction concentration on the paper's sets: " + "; ".join(f"{k}: {v['distinct_predicted_classes']} classes, top share {v['top_class_share']} %" for k, v in ref.items()), "",
           "## 2. Development test with a neutral clause (same 2,000 requests; exact %, 5 seeds)", "",
           "| model | original | clause before | clause after | long clause before | Δ before | Δ after | Δ long before |", "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for model in ("head", "decoder"):
        a = abl[model]
        def f(k):
            return f"{a[k]['mean']} ± {a[k]['sd']}" if k in a else "—"
        def g(k):
            return f"{a[k]['mean']:+.1f} [{a[k]['ci90'][0]:+.1f}, {a[k]['ci90'][1]:+.1f}] ({a[k]['seeds_negative']}/5 −)" if k in a else "—"
        md.append(f"| {model} | {f('original')} | {f('lead')} | {f('trail')} | {f('lead_long')} | {g('delta_lead')} | {g('delta_trail')} | {g('delta_lead_long')} |")
    (AB / "head_reversal.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---- figure
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), dpi=200)
    ax = axes[0]; forms = ["plain", "negation", "word_order", "context_clause"]; labels = ["plain", "negated\nintensity", "altered\norder", "context\nclause"]
    w = 0.38
    for k, (name, col) in enumerate((("decoder", "#d9534f"), ("head", "#2a9d6f"))):
        ax.bar([i + (k - 0.5) * w for i in range(4)], [reading[name][f]["colour_right"] for f in forms], w * 0.9, color=col, label=f"{name}: colour attribute right")
    ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=8); ax.set_ylim(0, 100); ax.set_ylabel("% of outputs with the right colour")
    ax.set_title("(a) Audited set: colour attribute of the predicted cell", fontsize=9.5); ax.legend(fontsize=7.5, frameon=False)
    ax = axes[1]
    xs = list(range(len(VARIANTS))); names = ["original", "clause\nbefore", "clause\nafter", "long clause\nbefore"]
    for name, col in (("decoder", "#d9534f"), ("head", "#2a9d6f")):
        ys = [abl[name].get(v, {}).get("mean", float("nan")) for v, _ in VARIANTS]; es = [abl[name].get(v, {}).get("sd", 0) for v, _ in VARIANTS]
        ax.errorbar(xs, ys, yerr=es, fmt="-o", color=col, capsize=3, label=name)
        for x, y in zip(xs, ys):
            ax.text(x, y + 2.5, f"{y:.1f}", ha="center", fontsize=7, color=col)
    ax.set_xticks(xs); ax.set_xticklabels(names, fontsize=8); ax.set_ylim(0, 100); ax.set_ylabel("development exact match (%)")
    ax.set_title("(b) Same requests with a neutral clause added", fontsize=9.5); ax.legend(fontsize=7.5, frameon=False)
    for a in axes:
        a.grid(axis="y", alpha=0.25)
        for s_ in ("top", "right"):
            a.spines[s_].set_visible(False)
    fig.patch.set_facecolor("white"); fig.tight_layout(); fig.savefig(HERE / "figures/F_head_ablation.png", facecolor="white"); plt.close(fig)
    print("\n".join(md[-4:])); print("  written", AB / "head_reversal.md")


if __name__ == "__main__":
    main()
