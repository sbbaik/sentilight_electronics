#!/usr/bin/env bash
# Vocabulary series (V): one pretrain+SFT+eval cycle per tokenizer (V4k V8k V16k V24k), d=384 L=8,
# K240 policy-only data. Reference point V24k-orig = W384 (backend/reports/scale_grid_width).
# Data first: python tools/build_vocab_series.py
# Usage:  tools/run_vocab_series.sh --dry-run | tools/run_vocab_series.sh | VOCABS="V4k" tools/run_vocab_series.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
VOCABS="${VOCABS:-V4k V8k V16k V24k}"
CONFIG=config/vocab_series.json
DATA=backend/models/compact_llm/datasets/keff_series/K240
VARIANT="${VARIANT:-}"   # "" = V1 (tokenizer trained on full corpus), "_natural" = V2 (KOTE lines only)
TOK_ROOT=backend/models/compact_llm/tokenizer_vocab_series$VARIANT
REPORT_BASE=backend/reports/scale_grid_vocab$VARIANT
RUN_BASE=backend/models/compact_llm/scale_grid_runs_vocab$VARIANT
mkdir -p "$REPORT_BASE"
{ sha256sum "$CONFIG" "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl";
  for V in $VOCABS; do sha256sum "$TOK_ROOT/$V/tokenizer.json" "$TOK_ROOT/$V/pretrain_tokens.npy"; done; } | tee "$REPORT_BASE/vocab_series.inputs.sha256"
for V in $VOCABS; do
  "$PY" tools/run_scale_grid.py \
    --scale-config "$CONFIG" --scales "$V" \
    --run-root "$RUN_BASE/$V" --report-root "$REPORT_BASE/$V" \
    --tokens-npy "$TOK_ROOT/$V/pretrain_tokens.npy" \
    --tokenizer-path "$TOK_ROOT/$V/tokenizer.json" \
    --subset-dir "$DATA" --val-jsonl "$DATA/val.jsonl" --dataset "$DATA/test_rule.jsonl" \
    --fractions 100 --seeds 42 43 44 \
    --pretrain-steps 2400 --sft-epochs 4 \
    --gpus 1 0 --max-parallel 2 \
    "$@"
done
