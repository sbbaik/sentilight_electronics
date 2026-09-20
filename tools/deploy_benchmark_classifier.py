"""CPU operating benchmark for the size-matched CompactLM-backbone 240-class classifier, under exactly the protocol
tools/deploy_benchmark.py uses for the generative models: same dataset, the same deterministic every-k-th subset,
the same 20 warm-up plus 300 timed prompts, 4 torch threads, one model per process so peak RSS is attributable.

Reports load time, RSS before and after load, peak RSS, median / p95 / mean latency, checkpoint size and the exact rate
on the timed subset. A classifier cannot emit invalid output, so the invalid-JSON column is zero by construction.
Usage: python tools/deploy_benchmark_classifier.py --checkpoint <clf_s42.pt> --out <json> [--threads 4] [--n 300]
"""
from __future__ import annotations
import argparse, json, os, resource, statistics as st, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
DIMS = ("H", "S", "B", "Dimmer", "CT")
def rss_mb():
    for line in open("/proc/self/status"):
        if line.startswith("VmRSS:"): return int(line.split()[1]) / 1024
    return float("nan")
ap = argparse.ArgumentParser()
ap.add_argument("--checkpoint", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--dataset", type=Path, default=REPO / "backend/models/compact_llm/datasets/keff_series/K240/test_rule.jsonl")
ap.add_argument("--n", type=int, default=300); ap.add_argument("--warmup", type=int, default=20)
ap.add_argument("--threads", type=int, default=4); ap.add_argument("--label", default="CompactLM backbone + 240-class head")
A = ap.parse_args()
os.environ["OMP_NUM_THREADS"] = str(A.threads)
import torch, torch.nn as nn
torch.set_num_threads(A.threads)
from compact_llm.model_definition import ModelConfig, SentilightCompactLM
from tokenizers import Tokenizer
rows = [json.loads(l) for l in A.dataset.open(encoding="utf-8") if l.strip()]
step = max(1, len(rows) // (A.n + A.warmup))
sample = rows[::step][: A.n + A.warmup]
rss_before = rss_mb()
t0 = time.perf_counter()
blob = torch.load(A.checkpoint, map_location="cpu", weights_only=False)
cfg = ModelConfig(**{k: v for k, v in blob["cfg"].items() if k in ModelConfig.__dataclass_fields__})
class Clf(nn.Module):
    def __init__(self, lm, n): super().__init__(); self.lm = lm; self.head = nn.Linear(lm.cfg.d_model, n)
    def forward(self, idx, mask):
        x = self.lm.tok_emb(idx)
        for b in self.lm.blocks: x = b(x)
        x = self.lm.norm_f(x)
        m = mask.unsqueeze(-1); return self.head((x * m).sum(1) / m.sum(1).clamp(min=1))
classes = [tuple(c) for c in blob["classes"]]
model = Clf(SentilightCompactLM(cfg), len(classes)); model.load_state_dict(blob["state_dict"]); model.eval()
tok = Tokenizer.from_file(str(REPO / "backend/models/compact_llm" / blob["tokenizer"] / "tokenizer.json"))
MAXLEN = blob.get("max_len", 64)
load_s = time.perf_counter() - t0
rss_after_load = rss_mb()
@torch.no_grad()
def predict(text):
    ids = tok.encode(text).ids[:MAXLEN] or [0]
    x = torch.tensor([ids]); m = torch.ones(1, len(ids))
    i = int(model(x, m).argmax(-1))
    return dict(zip(DIMS, (int(v) for v in classes[i])))
lat, exact = [], 0
for i, r in enumerate(sample):
    t = time.perf_counter(); pred = predict(str(r["input"])); dt = (time.perf_counter() - t) * 1000
    if i < A.warmup: continue
    lat.append(dt)
    exact += all(int(pred[k]) == int(r["output"][k]) for k in DIMS)
lat.sort(); n = len(lat)
out = {"label": A.label, "checkpoint": str(A.checkpoint), "checkpoint_mb": A.checkpoint.stat().st_size / 1e6,
       "device": "cpu", "torch_threads": torch.get_num_threads(), "cpu": os.uname().machine,
       "output_formulation": "240-class head (single forward pass)", "seeds_in_this_measurement": 1,
       "load_time_s": load_s, "rss_before_load_mb": rss_before, "rss_after_load_mb": rss_after_load,
       "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
       "n_timed": n, "latency_ms": {"median": lat[n // 2], "p95": lat[int(n * 0.95) - 1], "mean": st.mean(lat), "min": lat[0], "max": lat[-1]},
       "invalid_json_rate": 0.0, "invalid_note": "a 240-class head cannot emit an out-of-schema output",
       "exact_rate": exact / n, "protocol": "identical to tools/deploy_benchmark.py: same dataset, every-k-th subset, 20 warm-up + 300 timed, one model per process"}
A.out.parent.mkdir(parents=True, exist_ok=True); A.out.write_text(json.dumps(out, indent=1))
print(json.dumps({k: out[k] for k in ("label", "checkpoint_mb", "load_time_s", "rss_after_load_mb", "peak_rss_mb", "latency_ms", "exact_rate")}, indent=1))
