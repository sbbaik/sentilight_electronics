"""Instrumentation pass for the size-matched CompactLM-backbone 240-class classifier.

Why this exists: the frozen baseline run reported only aggregate accuracies, so the row-level comparison the analysis
needs (per-seed McNemar, seed->row bootstrap, per-attribute differences) and the CPU operating benchmark (load time,
peak RSS, p95 latency) could not be computed from what it saved. This script re-instantiates the SAME models with the
SAME seeds and configuration, dumps per-row predictions and checkpoints, and verifies that the per-seed accuracies
reproduce the frozen values. It introduces no new data, no new configuration and no new model choice; if the
reproduction check fails the discrepancy is reported rather than the new numbers being adopted.

Outputs backend/reports/baselines_nongenerative/classifier_instrumented/{per_row/*.jsonl, checkpoints/*.pt,
reproduction_check.json}.
Usage: python tools/instrument_compactlm_classifier.py [--device cuda:0]
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np
import torch, torch.nn as nn
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
from compact_llm.model_definition import ModelConfig, SentilightCompactLM  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402
M = REPO / "backend/models/compact_llm"; D = M / "datasets"
OUT = REPO / "backend/reports/baselines_nongenerative/classifier_instrumented"
(OUT / "per_row").mkdir(parents=True, exist_ok=True); (OUT / "checkpoints").mkdir(exist_ok=True)
DIMS = ("H", "S", "B", "Dimmer", "CT")
FROZEN = json.loads((REPO / "backend/reports/baselines_nongenerative/compactlm_classifier.json").read_text())
def load(p): return [json.loads(l) for l in Path(p).open(encoding="utf-8")]
def key(r): return tuple(int(r["output"][k]) for k in DIMS)
train = load(D / "keff_series/K240/train_100.jsonl"); val = load(D / "keff_series/K240/val.jsonl")
dev = load(D / "keff_series/K240/test_rule.jsonl"); hold = load(D / "holdout_natural/K240/holdout_2000.jsonl")
para = load(D / "holdout_paraphrase/K240/holdout_paraphrase.jsonl")
classes = sorted({key(r) for r in train}); cid = {c: i for i, c in enumerate(classes)}
ytr = np.array([cid[key(r)] for r in train])
tok = Tokenizer.from_file(str(M / "tokenizer_vocab_series_natural/V4k/tokenizer.json"))
MAXLEN = 64
def encode(rows):
    ids = [tok.encode(r["input"]).ids[:MAXLEN] for r in rows]
    n = max(len(x) for x in ids)
    X = np.zeros((len(ids), n), dtype=np.int64); Mk = np.zeros((len(ids), n), dtype=np.float32)
    for i, x in enumerate(ids): X[i, : len(x)] = x; Mk[i, : len(x)] = 1
    return torch.tensor(X), torch.tensor(Mk)
SETS = {k: encode(v) for k, v in (("train", train), ("val", val), ("dev", dev), ("hold", hold), ("para", para))}
Y = {k: torch.tensor([cid[key(r)] for r in v]) for k, v in (("train", train), ("val", val), ("dev", dev), ("hold", hold), ("para", para))}
ROWS = {"train": train, "val": val, "dev": dev, "hold": hold, "para": para}
class Clf(nn.Module):
    def __init__(self, lm, n): super().__init__(); self.lm = lm; self.head = nn.Linear(lm.cfg.d_model, n)
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
ap = argparse.ArgumentParser(); ap.add_argument("--device", default="cuda:0")
ap.add_argument("--epochs", type=int, default=4); ap.add_argument("--batch-size", type=int, default=64); ap.add_argument("--lr", type=float, default=3e-4)
A = ap.parse_args()
check = {"frozen_source": "backend/reports/baselines_nongenerative/compactlm_classifier.json", "seeds": {}}
for seed in (42, 43, 44, 45, 46):
    ck = M / f"scale_grid_runs_vocab_natural/V4k/V4k/seed_{seed}/pretrain/compactlm_pretrain_best.pt"
    blob = torch.load(ck, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**{k: v for k, v in blob["model_config"].items() if k in ModelConfig.__dataclass_fields__})
    lm = SentilightCompactLM(cfg); lm.load_state_dict(blob["model_state_dict"], strict=False)
    torch.manual_seed(seed); np.random.seed(seed)
    clf = Clf(lm, len(classes)).to(A.device)
    n_par = params_unique(clf)
    opt = torch.optim.AdamW(clf.parameters(), lr=A.lr, weight_decay=0.01); lossf = nn.CrossEntropyLoss()
    Xtr, Mtr = SETS["train"]; yt = Y["train"]; nb = (len(yt) + A.batch_size - 1) // A.batch_size
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=A.lr, total_steps=A.epochs * nb, pct_start=0.1)
    for ep in range(A.epochs):
        clf.train(); perm = torch.randperm(len(yt))
        for i in range(0, len(yt), A.batch_size):
            j = perm[i : i + A.batch_size]
            opt.zero_grad(); out = clf(Xtr[j].to(A.device), Mtr[j].to(A.device))
            loss = lossf(out, yt[j].to(A.device)); loss.backward()
            torch.nn.utils.clip_grad_norm_(clf.parameters(), 1.0); opt.step(); sched.step()
    @torch.no_grad()
    def pred(name, bs=256):
        clf.eval(); X, Mk = SETS[name]; o = []
        for i in range(0, len(X), bs): o.append(clf(X[i:i+bs].to(A.device), Mk[i:i+bs].to(A.device)).argmax(-1).cpu())
        return torch.cat(o)
    accs = {}
    for name in ("train", "val", "dev", "hold", "para"):
        p = pred(name); accs[name] = 100 * float((p == Y[name]).float().mean())
        if name in ("dev", "hold", "para"):
            with (OUT / "per_row" / f"clf_{name}_s{seed}.jsonl").open("w", encoding="utf-8") as f:
                for i, (pi, r) in enumerate(zip(p.tolist(), ROWS[name]), 1):
                    pt = classes[pi]
                    f.write(json.dumps({"row_index": i, "input": r["input"], "source": r.get("source", name),
                                        "reference": {k: int(r["output"][k]) for k in DIMS},
                                        "predicted": {k: int(v) for k, v in zip(DIMS, pt)},
                                        "success": True, "strict": None,
                                        "coarse": None}, ensure_ascii=False) + "\n")
    torch.save({"state_dict": clf.state_dict(), "classes": [list(c) for c in classes], "cfg": blob["model_config"], "seed": seed,
                "max_len": MAXLEN, "tokenizer": "tokenizer_vocab_series_natural/V4k"}, OUT / "checkpoints" / f"clf_s{seed}.pt")
    fr = FROZEN["seeds"][str(seed)]
    check["seeds"][seed] = {"params": n_par,
                            "reproduced": {k: round(accs[k2], 4) for k, k2 in (("dev_exact", "dev"), ("holdout_exact", "hold"), ("paraphrase_exact", "para"), ("train", "train"), ("val", "val"))},
                            "frozen": {k: fr[k] for k in ("dev_exact", "holdout_exact", "paraphrase_exact", "train", "val")},
                            "max_abs_diff_pp": max(abs(accs[k2] - fr[k]) for k, k2 in (("dev_exact", "dev"), ("holdout_exact", "hold"), ("paraphrase_exact", "para"), ("train", "train"), ("val", "val")))}
    print(f"seed {seed}: dev {accs['dev']:.2f} (frozen {fr['dev_exact']:.2f}) | frame {accs['hold']:.2f} ({fr['holdout_exact']:.2f}) | paraphrase {accs['para']:.2f} ({fr['paraphrase_exact']:.2f}) | max |Δ| {check['seeds'][seed]['max_abs_diff_pp']:.3f} pp", flush=True)
    del clf, lm; torch.cuda.empty_cache()
check["max_abs_diff_pp_overall"] = max(v["max_abs_diff_pp"] for v in check["seeds"].values())
check["verdict"] = "exact reproduction" if check["max_abs_diff_pp_overall"] < 1e-6 else ("reproduced within 0.1 pp" if check["max_abs_diff_pp_overall"] < 0.1 else "DOES NOT REPRODUCE - report the discrepancy, do not adopt")
json.dump(check, (OUT / "reproduction_check.json").open("w"), indent=1)
print("\nverdict:", check["verdict"], f"(max |Δ| {check['max_abs_diff_pp_overall']:.4f} pp)")
