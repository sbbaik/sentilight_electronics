#!/usr/bin/env bash
# Budget series (B): V2 V4k and V2 V24k tokenizers at 4,800 pretraining steps (2x), d=384 L=8, K240 data.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/budget_series.json
DATA=backend/models/compact_llm/datasets/keff_series/K240
REPORT_BASE=backend/reports/scale_grid_budget
RUN_BASE=backend/models/compact_llm/scale_grid_runs_budget
mkdir -p "$REPORT_BASE"
sha256sum "$CONFIG" "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl" \
  backend/models/compact_llm/tokenizer_vocab_series_natural/V4k/tokenizer.json backend/models/compact_llm/tokenizer_vocab_series_natural/V24k/tokenizer.json \
  | tee "$REPORT_BASE/budget.inputs.sha256"
for PAIR in "B4k V4k" "B24k V24k"; do set -- $PAIR; S=$1; V=$2
  TOK=backend/models/compact_llm/tokenizer_vocab_series_natural/$V
  "$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales "$S" \
    --run-root "$RUN_BASE/$S" --report-root "$REPORT_BASE/$S" \
    --tokens-npy "$TOK/pretrain_tokens.npy" --tokenizer-path "$TOK/tokenizer.json" \
    --subset-dir "$DATA" --val-jsonl "$DATA/val.jsonl" --dataset "$DATA/test_rule.jsonl" \
    --fractions 100 --seeds 42 43 44 --pretrain-steps 4800 --sft-epochs 4 --gpus 1 0 --max-parallel 2
done
