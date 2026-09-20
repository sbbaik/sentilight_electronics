"""Size-matched discriminative control: the SAME CompactLM backbone, same pretrained checkpoint, same fine-tuning rows,
but with a 240-class head instead of generative JSON decoding.

Why this exists: the Electronics review objected that the non-generative baselines were frozen-embedding straw men, and
an end-to-end fine-tuned 118 M multilingual encoder classifier turned out to beat the 15.7 M generative model on the
unseen-frame hold-out. That comparison confounds two things - architecture (classification vs generation) and the
pretrained encoder (118 M multilingual vs 15.7 M in-house Korean). This script removes the confound: it starts from the
identical pretrained CompactLM checkpoint of each seed, mean-pools the final hidden states, and trains a linear head
over the 240 executable tuples for the same number of epochs on the same rows. Any remaining difference is attributable
to the output formulation, not to the backbone.

Evaluates on the development test set and on the unseen-frame hold-out, and measures CPU latency (4 threads).
Writes backend/reports/baselines_nongenerative/compactlm_classifier.{json,md}.
Usage: python tools/compactlm_classifier_baseline.py [--seeds 42 43 44 45 46] [--epochs 4] [--device cuda:0]
"""
from __future__ import annotations
import argparse, json, os, statistics as st, sys, time
from pathlib import Path
import numpy as np
import torch, torch.nn as nn
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
from compact_llm.model_definition import ModelConfig, SentilightCompactLM  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402
M = REPO / "backend/models/compact_llm"; D = M / "datasets"; OUT = REPO / "backend/reports/baselines_nongenerative"
DIMS = ("H", "S", "B", "Dimmer", "CT")
def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def key(r): return tuple(int(r["output"][k]) for k in DIMS)

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
ap.add_argument("--epochs", type=int, default=4); ap.add_argument("--batch-size", type=int, default=64)
ap.add_argument("--lr", type=float, default=3e-4); ap.add_argument("--device", default="cuda:0"); ap.add_argument("--max-len", type=int, default=64)
A = ap.parse_args()

train = load(D / "keff_series/K240/train_100.jsonl"); val = load(D / "keff_series/K240/val.jsonl")
dev = load(D / "keff_series/K240/test_rule.jsonl"); hold = load(D / "holdout_natural/K240/holdout_2000.jsonl")
PARA = D / "holdout_paraphrase/K240/holdout_paraphrase.jsonl"
para = load(PARA) if PARA.exists() else []
classes = sorted({key(r) for r in train}); cid = {c: i for i, c in enumerate(classes)}
tok = Tokenizer.from_file(str(M / "tokenizer_vocab_series_natural/V4k/tokenizer.json"))
def encode(rows):
    ids = [tok.encode(r["input"]).ids[: A.max_len] for r in rows]
    n = max(len(x) for x in ids)
    X = np.zeros((len(ids), n), dtype=np.int64); Mk = np.zeros((len(ids), n), dtype=np.float32)
    for i, x in enumerate(ids): X[i, : len(x)] = x; Mk[i, : len(x)] = 1
    return torch.tensor(X), torch.tensor(Mk)
SETS = {k: encode(v) for k, v in (("train", train), ("val", val), ("dev", dev), ("hold", hold)) if v}
if para: SETS["para"] = encode(para)
Y = {k: torch.tensor([cid[key(r)] for r in v]) for k, v in (("train", train), ("val", val), ("dev", dev), ("hold", hold), ("para", para)) if v}
ROWS = {"train": train, "val": val, "dev": dev, "hold": hold, "para": para}

class Clf(nn.Module):
    def __init__(self, lm: SentilightCompactLM, n: int):
        super().__init__(); self.lm = lm; self.head = nn.Linear(lm.cfg.d_model, n)
    def forward(self, idx, mask):
        x = self.lm.tok_emb(idx)
        for b in self.lm.blocks: x = b(x)
        x = self.lm.norm_f(x)
        m = mask.unsqueeze(-1); return self.head((x * m).sum(1) / m.sum(1).clamp(min=1))

def params_unique(mod):
    seen, tot = set(), 0
    for p in mod.parameters():
        if p.data_ptr() in seen: continue
        seen.add(p.data_ptr()); tot += p.numel()
    return tot

res = {"seeds": {}, "classes": len(classes), "epochs": A.epochs, "lr": A.lr}
for seed in A.seeds:
    ck = M / f"scale_grid_runs_vocab_natural/V4k/V4k/seed_{seed}/pretrain/compactlm_pretrain_best.pt"
    if not ck.exists(): print(f"[skip] seed {seed}: {ck} missing"); continue
    blob = torch.load(ck, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**{k: v for k, v in blob["model_config"].items() if k in ModelConfig.__dataclass_fields__})
    lm = SentilightCompactLM(cfg); lm.load_state_dict(blob["model_state_dict"], strict=False)
    torch.manual_seed(seed); np.random.seed(seed)
    clf = Clf(lm, len(classes)).to(A.device)
    n_par = params_unique(clf) - cfg.vocab_size * cfg.d_model + cfg.vocab_size * cfg.d_model  # tied head removed, input embedding kept
    opt = torch.optim.AdamW(clf.parameters(), lr=A.lr, weight_decay=0.01); lossf = nn.CrossEntropyLoss()
    Xtr, Mtr = SETS["train"]; ytr = Y["train"]; nb = (len(ytr) + A.batch_size - 1) // A.batch_size
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=A.lr, total_steps=A.epochs * nb, pct_start=0.1)
    t0 = time.time()
    for ep in range(A.epochs):
        clf.train(); perm = torch.randperm(len(ytr)); tot = 0.0
        for i in range(0, len(ytr), A.batch_size):
            j = perm[i : i + A.batch_size]
            opt.zero_grad(); out = clf(Xtr[j].to(A.device), Mtr[j].to(A.device))
            loss = lossf(out, ytr[j].to(A.device)); loss.backward()
            torch.nn.utils.clip_grad_norm_(clf.parameters(), 1.0); opt.step(); sched.step(); tot += float(loss)
        print(f"  seed {seed} epoch {ep+1}/{A.epochs} loss {tot/nb:.4f} ({time.time()-t0:.0f}s)", flush=True)
    @torch.no_grad()
    def pred(name, bs=256):
        clf.eval(); X, Mk = SETS[name]; out = []
        for i in range(0, len(X), bs): out.append(clf(X[i:i+bs].to(A.device), Mk[i:i+bs].to(A.device)).argmax(-1).cpu())
        return torch.cat(out)
    accs = {}
    for name in [n for n in ("train", "val", "dev", "hold", "para") if n in SETS]:
        p = pred(name); accs[name] = 100 * float((p == Y[name]).float().mean())
    from collections import defaultdict
    ph = pred("hold"); g = defaultdict(list)
    for p, r in zip(ph.tolist(), hold): g[r["source"].replace("holdout_", "")].append(classes[p] == key(r))
    res["seeds"][seed] = {"params": n_par, "train": accs["train"], "val": accs["val"], "dev_exact": accs["dev"], "holdout_exact": accs["hold"], "paraphrase_exact": accs.get("para"),
                          "holdout_by_source": {k: round(100 * float(np.mean(v)), 1) for k, v in sorted(g.items())},
                          "distinct_predicted_classes_holdout": int(len(set(ph.tolist())))}
    print(f"seed {seed}: dev {accs['dev']:.1f} hold-out {accs['hold']:.1f} ({n_par/1e6:.2f} M)", flush=True)
    if seed == A.seeds[0]:
        torch.set_num_threads(4); os.environ["OMP_NUM_THREADS"] = "4"
        c = clf.to("cpu").eval(); texts = [r["input"] for r in hold]
        with torch.no_grad():
            for t in texts[:20]:
                x, m = encode([{"input": t}]); c(x, m)
            ts = []
            for t in texts[20:220]:
                x, m = encode([{"input": t}]); t1 = time.perf_counter(); c(x, m); ts.append((time.perf_counter() - t1) * 1000)
        res["cpu_median_ms"] = round(st.median(ts), 1); res["cpu_p95_ms"] = round(float(np.percentile(ts, 95)), 1)
    del clf, lm; torch.cuda.empty_cache()

S = res["seeds"]
if S:
    def ms(k): v = [S[s][k] for s in S]; return st.mean(v), (st.stdev(v) if len(v) > 1 else float("nan"))
    keys = [k for k in ("dev_exact", "holdout_exact", "paraphrase_exact", "train", "val") if S[list(S)[0]].get(k) is not None]
    res["summary"] = {k: {"mean": ms(k)[0], "sd": ms(k)[1], "per_seed": [S[s][k] for s in S]} for k in keys}
    res["params"] = S[list(S)[0]]["params"]
json.dump(res, (OUT / "compactlm_classifier.json").open("w"), indent=1, ensure_ascii=False)
L = ["# Size-matched discriminative control: CompactLM backbone with a 240-class head", "",
     f"Same pretrained checkpoints as the generative models (seeds {list(S)}), same {len(classes)} classes, {A.epochs} epochs, lr {A.lr}.", ""]
if S:
    L += [f"- parameters {res['params']:,} (generative model 15,698,304)", f"- development test exact {res['summary']['dev_exact']['mean']:.1f} ± {res['summary']['dev_exact']['sd']:.1f} %",
          f"- unseen-frame hold-out exact {res['summary']['holdout_exact']['mean']:.1f} ± {res['summary']['holdout_exact']['sd']:.1f} %",
          (f"- paraphrase hold-out exact {res['summary']['paraphrase_exact']['mean']:.1f} ± {res['summary']['paraphrase_exact']['sd']:.1f} %" if "paraphrase_exact" in res["summary"] else "- paraphrase hold-out: not available"),
          f"- per seed hold-out: {', '.join(f'{x:.1f}' for x in res['summary']['holdout_exact']['per_seed'])}",
          f"- CPU median latency {res.get('cpu_median_ms')} ms (4 threads)"]
(OUT / "compactlm_classifier.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
