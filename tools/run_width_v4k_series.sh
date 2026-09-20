#!/usr/bin/env bash
# Closing experiment X: d in {224,256,320}, L=8, V=4k natural tokenizer, 5 seeds. d=384 reference = V2 V4k.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/width_v4k_series.json
DATA=backend/models/compact_llm/datasets/keff_series/K240
TOK=backend/models/compact_llm/tokenizer_vocab_series_natural/V4k
REPORT_ROOT=backend/reports/scale_grid_width_v4k
RUN_ROOT=backend/models/compact_llm/scale_grid_runs_width_v4k
mkdir -p "$REPORT_ROOT"
sha256sum "$CONFIG" "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl" "$TOK/tokenizer.json" "$TOK/pretrain_tokens.npy" | tee "$REPORT_ROOT/inputs.sha256"
exec "$PY" tools/run_scale_grid.py --scale-config "$CONFIG" \
  --run-root "$RUN_ROOT" --report-root "$REPORT_ROOT" \
  --tokens-npy "$TOK/pretrain_tokens.npy" --tokenizer-path "$TOK/tokenizer.json" \
  --subset-dir "$DATA" --val-jsonl "$DATA/val.jsonl" --dataset "$DATA/test_rule.jsonl" \
  --fractions 100 --seeds 42 43 44 45 46 --pretrain-steps 2400 --sft-epochs 4 --gpus 1 0 --max-parallel 2 "$@"
