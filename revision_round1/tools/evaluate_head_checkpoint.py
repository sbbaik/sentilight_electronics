# -*- coding: utf-8 -*-
"""Evaluate a released 240-class head checkpoint (tools/compactlm_classifier_baseline.py layout:
state_dict / classes / cfg / seed / max_len / tokenizer) on a JSONL request set, writing per-row records in the
same shape as tools/evaluate_compactlm_checkpoint.py so one aggregation script serves every family.

Usage:
  python tools/evaluate_head_checkpoint.py --checkpoint models/head/clf_s42.pt --dataset <set.jsonl>
         --tokenizer-path <V4k/tokenizer.json> --model-id head240_s42 --per-row-jsonl out.jsonl --report-json out.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn

HERE = Path(__file__).resolve().parents[1]
CODE = HERE / "code"
sys.path.insert(0, str(CODE / "backend")); sys.path.insert(0, str(CODE / "backend/models"))
from compact_llm.model_definition import ModelConfig, SentilightCompactLM  # noqa: E402
from common.benchmark_eval import coarse_3bin_pass, normalize_lighting  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")


class Clf(nn.Module):                       # identical to the training script
    def __init__(self, lm: SentilightCompactLM, n: int):
        super().__init__(); self.lm = lm; self.head = nn.Linear(lm.cfg.d_model, n)

    def forward(self, idx, mask):
        x = self.lm.tok_emb(idx)
        for b in self.lm.blocks:
            x = b(x)
        x = self.lm.norm_f(x)
        m = mask.unsqueeze(-1); return self.head((x * m).sum(1) / m.sum(1).clamp(min=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True); ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--tokenizer-path", type=Path, required=True); ap.add_argument("--model-id", required=True)
    ap.add_argument("--display-name", default=None); ap.add_argument("--segment", default="rule")
    ap.add_argument("--device", default="cpu"); ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--per-row-jsonl", type=Path, required=True); ap.add_argument("--report-json", type=Path, required=True)
    ap.add_argument("--report-md", type=Path, default=None); ap.add_argument("--max-rows", type=int, default=None)
    A = ap.parse_args()
    torch.set_num_threads(max(1, torch.get_num_threads()))
    blob = torch.load(A.checkpoint, map_location="cpu", weights_only=False)
    cfg = ModelConfig(**blob["cfg"]); lm = SentilightCompactLM(cfg)
    classes = [tuple(int(v) for v in c) for c in blob["classes"]]
    clf = Clf(lm, len(classes)); clf.load_state_dict(blob["state_dict"]); clf.eval().to(A.device)
    max_len = int(blob.get("max_len", 64))
    tok = Tokenizer.from_file(str(A.tokenizer_path))
    rows = [json.loads(l) for l in A.dataset.open(encoding="utf-8")]
    if A.segment != "all":
        rows = [r for r in rows if r.get("segment", "rule") == A.segment] or rows
    if A.max_rows:
        rows = rows[: A.max_rows]
    A.per_row_jsonl.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_strict = n_coarse = 0; lat = []
    with A.per_row_jsonl.open("w", encoding="utf-8") as fh, torch.no_grad():
        for i in range(0, len(rows), A.batch_size):
            batch = rows[i:i + A.batch_size]
            ids = [tok.encode(r["input"]).ids[:max_len] for r in batch]
            n = max(len(x) for x in ids)
            X = torch.zeros((len(ids), n), dtype=torch.long); Mk = torch.zeros((len(ids), n))
            for j, x in enumerate(ids):
                X[j, :len(x)] = torch.tensor(x); Mk[j, :len(x)] = 1
            t0 = time.perf_counter()
            pred = clf(X.to(A.device), Mk.to(A.device)).argmax(-1).cpu().tolist()
            lat.append((time.perf_counter() - t0) * 1000 / len(batch))
            for k, (r, p) in enumerate(zip(batch, pred)):
                expected = normalize_lighting(r["output"]); predicted = dict(zip(DIMS, classes[p]))
                strict = all(int(expected[d]) == int(predicted[d]) for d in DIMS)
                coarse = coarse_3bin_pass(expected, predicted)
                n_ok += 1; n_strict += strict; n_coarse += coarse
                fh.write(json.dumps({"mode": "head_checkpoint", "row_index": i + k + 1, "source": r.get("source"),
                                     "model_id": A.model_id, "display_name": A.display_name or A.model_id,
                                     "adapter": "tuple_classifier", "model_mode": "head_checkpoint", "input": r["input"],
                                     "emotion": r.get("emotion"), "base_color": r.get("base_color"), "intensity": r.get("intensity"),
                                     "reference": expected, "success": True, "predicted": predicted, "raw": predicted,
                                     "error": None, "strict": strict, "coarse": coarse,
                                     "latency_ms_batch_mean": round(lat[-1], 3)}, ensure_ascii=False) + "\n")
    rep = {"model_id": A.model_id, "checkpoint": str(A.checkpoint), "rows": n_ok, "strict": n_strict,
           "strict_pct": round(100 * n_strict / n_ok, 2), "coarse": n_coarse, "coarse_pct": round(100 * n_coarse / n_ok, 2),
           "classes": len(classes), "max_len": max_len, "tokenizer": str(A.tokenizer_path),
           "note": "batched forward pass; per-row latency not a deployment measurement"}
    A.report_json.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    if A.report_md:
        A.report_md.write_text(f"# {A.model_id}\n\nrows {n_ok}, strict {rep['strict_pct']} %, coarse {rep['coarse_pct']} %\n", encoding="utf-8")
    print(f"{A.model_id}: rows {n_ok} strict {rep['strict_pct']}% coarse {rep['coarse_pct']}%")


if __name__ == "__main__":
    main()
