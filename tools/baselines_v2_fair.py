"""Fair non-generative baselines and diagnostics for the 240-tuple control task (Electronics revision).

Answers the review's baseline objections:
  (1) diagnostics of the frozen-SBERT pipeline (why it is weak): class coverage, label alignment, embedding
      normalisation, class imbalance, number of distinct predicted classes, top-class share, train/val/dev/hold-out;
  (2) a genuinely competitive discriminative baseline: the multilingual MiniLM encoder FINE-TUNED end-to-end with a
      240-class head on the same 49,093 SFT rows (not a frozen-embedding straw man);
  (3) the system's own deployed non-generative path: the fine-tuned SBERT adapter with prototype matching over
      profiles.json, evaluated with the same exact-tuple metric.
All models are evaluated on the development test set and on the unseen-frame hold-out, with file size and CPU latency
(4 threads). Writes backend/reports/baselines_nongenerative/{fair_results.json, fair_results.md}.
Usage: python tools/baselines_v2_fair.py [--epochs 3] [--device cuda:0]
"""
from __future__ import annotations
import argparse, json, os, statistics as st, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
D = REPO / "backend/models/compact_llm/datasets"; OUT = REPO / "backend/reports/baselines_nongenerative"
OUT.mkdir(parents=True, exist_ok=True)
DIMS = ("H", "S", "B", "Dimmer", "CT")
ENC = REPO / "backend/models/sbert_emotion/model"              # frozen multilingual MiniLM (local copy)
FT = REPO / "backend/models/sbert_emotion/finetuned_model"      # deployed fine-tuned encoder
PROFILES = REPO / "backend/models/sbert_emotion/profiles.json"

def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def key(r): return tuple(int(r["output"][k]) for k in DIMS)
train = load(D / "keff_series/K240/train_100.jsonl"); val = load(D / "keff_series/K240/val.jsonl")
dev = load(D / "keff_series/K240/test_rule.jsonl"); hold = load(D / "holdout_natural/K240/holdout_2000.jsonl")
PARA = D / "holdout_paraphrase/K240/holdout_paraphrase.jsonl"
para = load(PARA) if PARA.exists() else []
classes = sorted({key(r) for r in train}); cid = {c: i for i, c in enumerate(classes)}
ytr = np.array([cid[key(r)] for r in train])
TXT = {"train": [r["input"] for r in train], "val": [r["input"] for r in val], "dev": [r["input"] for r in dev], "hold": [r["input"] for r in hold]}
if para: TXT["para"] = [r["input"] for r in para]
GOLD = {"train": train, "val": val, "dev": dev, "hold": hold, "para": para}
def acc(pred_ids, rows): return 100 * float(np.mean([classes[p] == key(r) for p, r in zip(pred_ids, rows)]))
def by_source(pred_ids, rows):
    g = defaultdict(list)
    for p, r in zip(pred_ids, rows): g[r.get("source", "dev").replace("holdout_", "")].append(classes[p] == key(r))
    return {k: round(100 * float(np.mean(v)), 1) for k, v in sorted(g.items())}

ap = argparse.ArgumentParser(); ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--device", default="cuda:0")
ap.add_argument("--batch-size", type=int, default=64); ap.add_argument("--lr", type=float, default=3e-5)
A = ap.parse_args()
import torch
results, diag = {}, {}

# ---------------------------------------------------------------- 0. dataset / label diagnostics
cnt = Counter(key(r) for r in train)
diag["dataset"] = {"train_rows": len(train), "classes_in_train": len(classes), "reachable_tuples": 240,
                   "classes_missing_from_train": 240 - len(classes),
                   "rows_per_class_min": min(cnt.values()), "rows_per_class_median": int(st.median(cnt.values())), "rows_per_class_max": max(cnt.values()),
                   "imbalance_max_over_min": round(max(cnt.values()) / min(cnt.values()), 2),
                   "dev_classes_unseen_in_train": len({key(r) for r in dev} - set(classes)),
                   "holdout_classes_unseen_in_train": len({key(r) for r in hold} - set(classes)),
                   "label_alignment_check": "classes sorted once; cid maps tuple->index; predictions decoded via classes[i]"}

# ---------------------------------------------------------------- 1. frozen SBERT diagnostics (why the baseline is weak)
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
frozen = SentenceTransformer(str(ENC) if ENC.exists() else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device=A.device)
def embed(model, texts, bs=256): return model.encode(texts, batch_size=bs, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
E = {k: embed(frozen, v) for k, v in TXT.items()}
diag["frozen_sbert"] = {"embedding_dim": int(E["train"].shape[1]), "norm_mean": float(np.linalg.norm(E["train"], axis=1).mean()),
                        "distinct_train_embeddings": int(len(np.unique(np.round(E["train"], 4), axis=0))),
                        "note": "vectors are L2-normalised (norm 1.0); distinct-embedding count shows how many training utterances the frozen encoder separates at all"}
best = None
for C in (1.0, 4.0, 16.0, 64.0):
    lr = LogisticRegression(C=C, max_iter=1000, n_jobs=8).fit(E["train"], ytr); a = acc(lr.predict(E["val"]), val)
    if best is None or a > best[0]: best = (a, C, lr)
val_acc, C, lr = best
pred = {k: lr.predict(E[k]) for k in TXT}
results["sbert_frozen_logreg"] = {"C": C, "train_exact": acc(pred["train"], train), "val_exact": val_acc, "dev_exact": acc(pred["dev"], dev), "holdout_exact": acc(pred["hold"], hold), "paraphrase_exact": (acc(pred["para"], para) if para else None),
                                  "holdout_by_source": by_source(pred["hold"], hold),
                                  "distinct_predicted_classes_dev": int(len(set(pred["dev"].tolist()))), "top_class_share_dev": round(100 * Counter(pred["dev"].tolist()).most_common(1)[0][1] / len(dev), 1),
                                  "encoder_params_M": sum(p.numel() for p in frozen.parameters()) / 1e6}
print("frozen sbert:", json.dumps(results["sbert_frozen_logreg"], ensure_ascii=False))

# ---------------------------------------------------------------- 2. deployed fine-tuned SBERT + logistic head
ftm = SentenceTransformer(str(FT), device=A.device) if FT.exists() else None
if ftm is not None:
    Ef = {k: embed(ftm, v) for k, v in TXT.items()}
    best = None
    for C in (1.0, 4.0, 16.0, 64.0):
        lr2 = LogisticRegression(C=C, max_iter=1000, n_jobs=8).fit(Ef["train"], ytr); a = acc(lr2.predict(Ef["val"]), val)
        if best is None or a > best[0]: best = (a, C, lr2)
    val_acc2, C2, lr2 = best; pred2 = {k: lr2.predict(Ef[k]) for k in TXT}
    results["sbert_deployed_finetuned_logreg"] = {"C": C2, "train_exact": acc(pred2["train"], train), "val_exact": val_acc2, "dev_exact": acc(pred2["dev"], dev),
                                                  "holdout_exact": acc(pred2["hold"], hold), "paraphrase_exact": (acc(pred2["para"], para) if para else None), "holdout_by_source": by_source(pred2["hold"], hold),
                                                  "encoder_params_M": sum(p.numel() for p in ftm.parameters()) / 1e6,
                                                  "note": "encoder fine-tuned for the deployed similarity objective, head trained here"}
    print("deployed ft sbert + logreg:", json.dumps(results["sbert_deployed_finetuned_logreg"], ensure_ascii=False))

# ---------------------------------------------------------------- 3. deployed SBERT adapter (prototype matching)
if ftm is not None and PROFILES.exists():
    prof = json.loads(PROFILES.read_text(encoding="utf-8")); prof = prof.get("profiles", prof)
    proto_txt, proto_idx = [], []
    for i, p in enumerate(prof):
        for ex in p.get("examples", []): proto_txt.append(str(ex)); proto_idx.append(i)
    Ep = embed(ftm, proto_txt); proto_idx = np.array(proto_idx)
    ptuple = [tuple(int(p["lighting"][k]) for k in DIMS) for p in prof]
    reachable = len(set(ptuple) & set(classes))
    def adapter_pred(E_):
        nn = np.argmax(E_ @ Ep.T, axis=1); return [ptuple[proto_idx[i]] for i in nn]
    def acc_t(tuples, rows): return 100 * float(np.mean([t == key(r) for t, r in zip(tuples, rows)]))
    pd_, ph_ = adapter_pred(Ef["dev"]), adapter_pred(Ef["hold"])
    g = defaultdict(list)
    for t, r in zip(ph_, hold): g[r["source"].replace("holdout_", "")].append(t == key(r))
    results["sbert_deployed_adapter_prototype"] = {"profiles": len(prof), "prototype_examples": len(proto_txt), "profile_tuples_within_240": reachable,
                                                   "unreachable_tuples": 240 - reachable, "dev_exact": acc_t(pd_, dev), "holdout_exact": acc_t(ph_, hold),
                                                   "holdout_by_source": {k: round(100 * float(np.mean(v)), 1) for k, v in sorted(g.items())},
                                                   "note": "the deployed SBERT condition: fine-tuned encoder, nearest prototype example, profile's lighting tuple"}
    print("deployed adapter:", json.dumps(results["sbert_deployed_adapter_prototype"], ensure_ascii=False))

# ---------------------------------------------------------------- 4. end-to-end fine-tuned 240-class classifier
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModel
tok = AutoTokenizer.from_pretrained(str(ENC) if ENC.exists() else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
base = AutoModel.from_pretrained(str(ENC) if ENC.exists() else "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
class Clf(torch.nn.Module):
    def __init__(self, enc, n): super().__init__(); self.enc = enc; self.head = torch.nn.Linear(enc.config.hidden_size, n)
    def forward(self, ids, mask):
        h = self.enc(input_ids=ids, attention_mask=mask).last_hidden_state
        m = mask.unsqueeze(-1).float(); return self.head((h * m).sum(1) / m.sum(1))
clf = Clf(base, len(classes)).to(A.device)
def enc_batch(texts): 
    b = tok(texts, padding=True, truncation=True, max_length=64, return_tensors="pt"); return b["input_ids"], b["attention_mask"]
ids, mask = enc_batch(TXT["train"]); ds = TensorDataset(ids, mask, torch.tensor(ytr))
dl = DataLoader(ds, batch_size=A.batch_size, shuffle=True)
opt = torch.optim.AdamW(clf.parameters(), lr=A.lr); lossf = torch.nn.CrossEntropyLoss()
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=A.lr, total_steps=A.epochs * len(dl), pct_start=0.1)
t0 = time.time()
for ep in range(A.epochs):
    clf.train(); tot = 0.0
    for bi, bm, by in dl:
        opt.zero_grad(); out = clf(bi.to(A.device), bm.to(A.device)); loss = lossf(out, by.to(A.device)); loss.backward(); opt.step(); sched.step(); tot += float(loss)
    print(f"  ft-clf epoch {ep+1}/{A.epochs} loss {tot/len(dl):.4f} ({time.time()-t0:.0f}s)")
@torch.no_grad()
def clf_pred(texts, bs=256):
    clf.eval(); out = []
    for i in range(0, len(texts), bs):
        bi, bm = enc_batch(texts[i:i + bs]); out.append(clf(bi.to(A.device), bm.to(A.device)).argmax(-1).cpu().numpy())
    return np.concatenate(out)
pc = {k: clf_pred(v) for k, v in TXT.items()}
ckpt = OUT / "finetuned_240class.pt"; torch.save({"state_dict": clf.state_dict(), "classes": [list(c) for c in classes]}, ckpt)
results["encoder_finetuned_240class"] = {"epochs": A.epochs, "lr": A.lr, "train_exact": acc(pc["train"], train), "val_exact": acc(pc["val"], val),
                                         "dev_exact": acc(pc["dev"], dev), "holdout_exact": acc(pc["hold"], hold), "paraphrase_exact": (acc(pc["para"], para) if para else None), "holdout_by_source": by_source(pc["hold"], hold),
                                         "params_M": sum(p.numel() for p in clf.parameters()) / 1e6, "file_mb": ckpt.stat().st_size / 1e6,
                                         "distinct_predicted_classes_holdout": int(len(set(pc["hold"].tolist())))}
print("finetuned 240-class:", json.dumps(results["encoder_finetuned_240class"], ensure_ascii=False))

# ---------------------------------------------------------------- 5. CPU latency (4 threads) for the two encoder paths
torch.set_num_threads(4); os.environ["OMP_NUM_THREADS"] = "4"
def latency(fn, texts, n=200, warm=20):
    for t in texts[:warm]: fn(t)
    ts = []
    for t in texts[warm:warm + n]:
        t0 = time.perf_counter(); fn(t); ts.append((time.perf_counter() - t0) * 1000)
    return round(st.median(ts), 1), round(float(np.percentile(ts, 95)), 1)
clf_cpu = clf.to("cpu"); clf_cpu.eval()
@torch.no_grad()
def one(t):
    bi, bm = enc_batch([t]); return clf_cpu(bi, bm).argmax(-1)
m, p95 = latency(one, TXT["hold"]); results["encoder_finetuned_240class"].update({"cpu_median_ms": m, "cpu_p95_ms": p95})
if ftm is not None:
    ftc = ftm.to("cpu")
    m2, p2 = latency(lambda t: ftc.encode([t], normalize_embeddings=True, show_progress_bar=False), TXT["hold"], n=100)
    for k in ("sbert_deployed_finetuned_logreg", "sbert_deployed_adapter_prototype"):
        if k in results: results[k].update({"cpu_median_ms": m2, "cpu_p95_ms": p2})

json.dump({"diagnostics": diag, "results": results}, (OUT / "fair_results.json").open("w"), indent=1, ensure_ascii=False)
L = ["# Non-generative baselines, fair comparison and diagnostics", "",
     f"Training rows {len(train)}; classes present in training {len(classes)}/240; rows per class min {diag['dataset']['rows_per_class_min']}, median {diag['dataset']['rows_per_class_median']}, max {diag['dataset']['rows_per_class_max']}.", "",
     "| model | train | val | dev test | unseen-frame hold-out | paraphrase hold-out | CPU median ms | note |", "|---|--:|--:|--:|--:|--:|--:|---|"]
for k, r in results.items():
    pe = r.get("paraphrase_exact")
    L.append(f"| {k} | {r.get('train_exact', float('nan')):.1f} | {r.get('val_exact', float('nan')):.1f} | {r['dev_exact']:.1f} | {r['holdout_exact']:.1f} | {(f'{pe:.1f}' if pe is not None else '—')} | {r.get('cpu_median_ms', float('nan'))} | {r.get('note', '')} |")
L += ["", "Diagnostics:", "```", json.dumps(diag, ensure_ascii=False, indent=1), "```"]
(OUT / "fair_results.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L[:12]))
