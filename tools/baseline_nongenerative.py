"""Non-generative baselines for the K240 policy: predict the executable tuple as a 240-class label.
  (a) TF-IDF character n-grams (2-4) + multinomial logistic regression
  (b) frozen SBERT sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2, local cache) + logistic regression
  (c) SBERT nearest-centroid (no trained head)
Trained on K240 train_100 (49,093 rows, same data as the SFT models), model selected on K240 val (no test access),
evaluated on the development test (test_rule, 2,000 rows) and on the untouched hold-out (holdout_2000).
Also reports model file size and CPU latency (4 threads, 300 prompts after 20 warm-up).
Writes backend/reports/baselines_nongenerative/{results.json, results.md}.
"""
from __future__ import annotations
import json, os, pickle, statistics as st, sys, time
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[1]
D = REPO / "backend/models/compact_llm/datasets"; OUT = REPO / "backend/reports/baselines_nongenerative"; OUT.mkdir(parents=True, exist_ok=True)
DIMS = ("H", "S", "B", "Dimmer", "CT")
def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def key(r): return tuple(int(r["output"][k]) for k in DIMS)
train = load(D / "keff_series/K240/train_100.jsonl"); val = load(D / "keff_series/K240/val.jsonl")
dev = load(D / "keff_series/K240/test_rule.jsonl"); hold = load(D / "holdout_natural/K240/holdout_2000.jsonl")
classes = sorted({key(r) for r in train}); cid = {c: i for i, c in enumerate(classes)}
ytr = np.array([cid[key(r)] for r in train]); Xtr_txt = [r["input"] for r in train]
def acc(pred_ids, rows): return 100 * float(np.mean([classes[p] == key(r) for p, r in zip(pred_ids, rows)]))
os.environ.setdefault("OMP_NUM_THREADS", "4"); import torch; torch.set_num_threads(4)
results = {}

# ---- (a) TF-IDF char n-gram + logistic regression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
best = None
for C in (1.0, 4.0, 16.0):
    pipe = make_pipeline(TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=2, sublinear_tf=True), LogisticRegression(C=C, max_iter=300, n_jobs=4))
    pipe.fit(Xtr_txt, ytr); a = acc(pipe.predict([r["input"] for r in val]), val)
    if best is None or a > best[0]: best = (a, C, pipe)
val_acc, C, pipe = best
def latency(fn, texts, n=300, warm=20):
    for t in texts[:warm]: fn(t)
    ts = []
    for t in texts[warm:warm + n]:
        t0 = time.perf_counter(); fn(t); ts.append((time.perf_counter() - t0) * 1000)
    return st.median(ts), float(np.percentile(ts, 95))
pk = OUT / "tfidf_logreg.pkl"; pickle.dump(pipe, pk.open("wb"))
med, p95 = latency(lambda t: pipe.predict([t]), [r["input"] for r in hold])
results["tfidf_char_logreg"] = {"val_acc": val_acc, "C": C, "dev_exact": acc(pipe.predict([r["input"] for r in dev]), dev), "holdout_exact": acc(pipe.predict([r["input"] for r in hold]), hold),
                                "file_mb": pk.stat().st_size / 1e6, "n_features": int(pipe[0].transform(["x"]).shape[1]), "cpu_median_ms": med, "cpu_p95_ms": p95}
print("tfidf:", results["tfidf_char_logreg"])

# ---- (b)(c) SBERT
from sentence_transformers import SentenceTransformer
sb = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
def emb(texts): return sb.encode(texts, batch_size=128, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
Etr, Eval, Edev, Ehold = emb(Xtr_txt), emb([r["input"] for r in val]), emb([r["input"] for r in dev]), emb([r["input"] for r in hold])
best = None
for C in (1.0, 4.0, 16.0):
    lr = LogisticRegression(C=C, max_iter=500, n_jobs=4).fit(Etr, ytr); a = acc(lr.predict(Eval), val)
    if best is None or a > best[0]: best = (a, C, lr)
val_acc, C, lr = best
n_params = sum(p.numel() for p in sb.parameters()); size_mb = sum(f.stat().st_size for f in Path(sb[0].auto_model.config._name_or_path).rglob("*.safetensors")) / 1e6 if Path(sb[0].auto_model.config._name_or_path).exists() else float("nan")
med, p95 = latency(lambda t: lr.predict(emb([t])), [r["input"] for r in hold])
results["sbert_logreg"] = {"val_acc": val_acc, "C": C, "dev_exact": acc(lr.predict(Edev), dev), "holdout_exact": acc(lr.predict(Ehold), hold), "encoder_params_M": n_params / 1e6,
                           "encoder_file_mb": size_mb, "head_params_M": lr.coef_.size / 1e6, "cpu_median_ms": med, "cpu_p95_ms": p95}
print("sbert+logreg:", results["sbert_logreg"])
cent = np.zeros((len(classes), Etr.shape[1]))
for i in range(len(classes)): cent[i] = Etr[ytr == i].mean(0)
cent /= np.linalg.norm(cent, axis=1, keepdims=True)
def nc(E): return np.argmax(E @ cent.T, axis=1)
med, p95 = latency(lambda t: nc(emb([t])), [r["input"] for r in hold])
results["sbert_nearest_centroid"] = {"dev_exact": acc(nc(Edev), dev), "holdout_exact": acc(nc(Ehold), hold), "encoder_params_M": n_params / 1e6, "cpu_median_ms": med, "cpu_p95_ms": p95}
print("sbert nearest-centroid:", results["sbert_nearest_centroid"])
# by source on holdout for the two trained baselines
from collections import defaultdict
def by_source(pred, rows):
    g = defaultdict(list)
    for p, r in zip(pred, rows): g[r["source"]].append(classes[p] == key(r))
    return {k: 100 * float(np.mean(v)) for k, v in g.items()}
results["tfidf_char_logreg"]["holdout_by_source"] = by_source(pipe.predict([r["input"] for r in hold]), hold)
results["sbert_logreg"]["holdout_by_source"] = by_source(lr.predict(Ehold), hold)
json.dump({"classes": len(classes), "train_rows": len(train), "results": results}, (OUT / "results.json").open("w"), indent=1)
L = ["# Non-generative baselines (240-class prediction of the executable tuple)", "", f"Trained on K240 train_100 ({len(train)} rows), C chosen on val; invalid outputs are impossible by construction.", "",
     "| model | dev test exact % | hold-out exact % | size | CPU median / p95 ms (4 threads) |", "|---|--:|--:|---|--:|"]
r = results["tfidf_char_logreg"]; L.append(f"| TF-IDF char 2–4-gram + logistic regression | {r['dev_exact']:.1f} | {r['holdout_exact']:.1f} | {r['file_mb']:.1f} MB pickle, {r['n_features']:,} features | {r['cpu_median_ms']:.1f} / {r['cpu_p95_ms']:.1f} |")
r = results["sbert_logreg"]; L.append(f"| SBERT (MiniLM-L12 multilingual, frozen) + logistic regression | {r['dev_exact']:.1f} | {r['holdout_exact']:.1f} | encoder {r['encoder_params_M']:.0f} M params ({r['encoder_file_mb']:.0f} MB) + head {r['head_params_M']:.2f} M | {r['cpu_median_ms']:.1f} / {r['cpu_p95_ms']:.1f} |")
r = results["sbert_nearest_centroid"]; L.append(f"| SBERT nearest centroid (no trained head) | {r['dev_exact']:.1f} | {r['holdout_exact']:.1f} | encoder {r['encoder_params_M']:.0f} M params | {r['cpu_median_ms']:.1f} / {r['cpu_p95_ms']:.1f} |")
L += ["", "Hold-out exact % by source: " + json.dumps({k: {s: round(v, 1) for s, v in results[k]["holdout_by_source"].items()} for k in ("tfidf_char_logreg", "sbert_logreg")}, ensure_ascii=False)]
(OUT / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
