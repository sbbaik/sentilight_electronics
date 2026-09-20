#!/usr/bin/env bash
# Combined cell C4kL4: d=384, L=4, V=4k natural tokenizer, K240 data. 3 seeds, pretrain+SFT+eval.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/combo_series.json
DATA=backend/models/compact_llm/datasets/keff_series/K240
TOK=backend/models/compact_llm/tokenizer_vocab_series_natural/V4k
REPORT_ROOT=backend/reports/scale_grid_combo
RUN_ROOT=backend/models/compact_llm/scale_grid_runs_combo
mkdir -p "$REPORT_ROOT"
sha256sum "$CONFIG" "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl" "$TOK/tokenizer.json" "$TOK/pretrain_tokens.npy" | tee "$REPORT_ROOT/combo.inputs.sha256"
exec "$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales C4kL4 \
  --run-root "$RUN_ROOT" --report-root "$REPORT_ROOT" \
  --tokens-npy "$TOK/pretrain_tokens.npy" --tokenizer-path "$TOK/tokenizer.json" \
  --subset-dir "$DATA" --val-jsonl "$DATA/val.jsonl" --dataset "$DATA/test_rule.jsonl" \
  --fractions 100 --seeds 42 43 44 --pretrain-steps 2400 --sft-epochs 4 --gpus 1 0 --max-parallel 2 "$@"
