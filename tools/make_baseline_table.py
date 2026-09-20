"""Build tables/T14_baselines_vs_compactlm.csv from the three baseline result files and the hold-out analysis.

Rows are ordered from the weakest lexical baseline to the generative model under study, and the table carries the two
facts the Electronics review asked for: what each model costs (parameters, file size, CPU latency) and how it behaves on
the unseen-frame hold-out, not only on the development test set. The size-matched CompactLM-backbone classifier is the
row that separates 'classification vs generation' from 'which pretrained backbone', because it shares the backbone and
the pretrained checkpoints with the generative model.
"""
from __future__ import annotations
import csv, json, statistics as st
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; OUT = REPO / "backend/reports/baselines_nongenerative"; TAB = REPO.parent / "tables"
fair = json.loads((OUT / "fair_results.json").read_text(encoding="utf-8"))
old = json.loads((OUT / "results.json").read_text(encoding="utf-8"))["results"]
clf = json.loads((OUT / "compactlm_classifier.json").read_text(encoding="utf-8"))
hold = json.loads((REPO / "backend/reports/holdout_final/analysis.json").read_text(encoding="utf-8"))
PARA_F = REPO / "backend/reports/holdout_paraphrase/analysis.json"
para = json.loads(PARA_F.read_text(encoding="utf-8")) if PARA_F.exists() else {"configs": {}}
def pcell(v): return "—" if v is None else (f"{v:.1f}" if isinstance(v, (int, float)) else str(v))
F = fair["results"]
def pm(m, s): return f"{m:.1f} ± {s:.1f}"
rows = [["model", "seeds", "output formulation", "parameters", "model file", "development test exact %", "unseen-frame hold-out exact %", "paraphrase stress-set exact %", "CPU median latency, ms (4 threads)", "invalid outputs"]]
r = old["tfidf_char_logreg"]
rows.append(["TF-IDF character 2–4-grams + logistic regression", "1 (descriptive only)", "240-class", f"{r['n_features']:,} × 240 weights", f"{r['file_mb']:.1f} MB", f"{r['dev_exact']:.1f}", f"{r['holdout_exact']:.1f}", pcell(r.get("paraphrase_exact")), f"{r['cpu_median_ms']:.1f}", "impossible by construction"])
r = F["sbert_frozen_logreg"]
rows.append(["frozen multilingual MiniLM-L12 embeddings + logistic regression", "1 (descriptive only)", "240-class", f"{r['encoder_params_M']:.0f} M encoder (frozen) + 0.09 M head", "471 MB encoder", f"{r['dev_exact']:.1f}", f"{r['holdout_exact']:.1f}", pcell(r.get("paraphrase_exact")), f"{old['sbert_logreg']['cpu_median_ms']:.1f}", "impossible by construction"])
r = old["sbert_nearest_centroid"]
rows.append(["frozen multilingual MiniLM-L12, nearest class centroid", "1 (descriptive only)", "240-class", f"{r['encoder_params_M']:.0f} M encoder (frozen), no head", "471 MB encoder", f"{r['dev_exact']:.1f}", f"{r['holdout_exact']:.1f}", pcell(r.get("paraphrase_exact")), f"{r['cpu_median_ms']:.1f}", "impossible by construction"])
r = F["encoder_finetuned_240class"]
rows.append(["multilingual MiniLM-L12 fine-tuned end to end + 240-class head", "**1 (descriptive only)**", "240-class", f"{r['params_M']:.0f} M", f"{r['file_mb']:.0f} MB", f"{r['dev_exact']:.1f}", f"{r['holdout_exact']:.1f}", pcell(r.get("paraphrase_exact")), f"{r['cpu_median_ms']:.1f}", "impossible by construction"])
s = clf.get("summary")
if s:
    rows.append(["CompactLM backbone (same pretrained checkpoints) + 240-class head", "5", "240-class", f"{clf['params']/1e6:.1f} M", f"{clf['params']*4/1e6:.0f} MB fp32",
                 pm(s["dev_exact"]["mean"], s["dev_exact"]["sd"]), pm(s["holdout_exact"]["mean"], s["holdout_exact"]["sd"]),
                 (pm(s["paraphrase_exact"]["mean"], s["paraphrase_exact"]["sd"]) if "paraphrase_exact" in s else "—"), f"{clf.get('cpu_median_ms','—')}", "impossible by construction"])
for cfg, label, extra in (("deployed_W384_L8_V24k", "CompactLM, deployed architecture (d 384, L 8, 24k)", ("93.5 MB fp32", "101")),
                          ("selected_V4k_L8", "CompactLM, selected model (d 384, L 8, 4k natural)", ("62.8 MB fp32; 17.1 MB mixed-bit", "95"))):
    c = hold["configs"][cfg]
    pc = para["configs"].get(cfg)
    rows.append([label, "5", "generative JSON", f"{c['params']/1e6:.1f} M", extra[0], pm(c["dev_mean"], c["dev_sd"]), pm(c["mean"], c["sd"]),
                 (pm(pc["mean"], pc["sd"]) if pc else "—"), extra[1], f"{100-c['valid_pct']:.1f} %"])
with (TAB / "T14_baselines_vs_compactlm.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(rows)
print("\n".join(" | ".join(r) for r in rows))
