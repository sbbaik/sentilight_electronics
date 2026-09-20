#!/usr/bin/env bash
# Width series (W): d_model sweep at fixed depth/vocab/compute on the clean corpus.
# Usage:
#   tools/run_width_series.sh --dry-run            # print the 63 task commands, write nothing else
#   tools/run_width_series.sh                      # full run: pretrain -> sft -> eval
#   tools/run_width_series.sh --scales W224 W256   # subset
#   tools/run_width_series.sh --phases eval        # re-run one phase
# After the run:
#   python tools/summarize_scale_grid.py --report-root backend/reports/scale_grid_width \
#       --report-json backend/reports/scale_grid_width/scale_grid_summary.json \
#       --report-md   backend/reports/scale_grid_width/scale_grid_summary.md
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/width_series.json
RUN_ROOT=backend/models/compact_llm/scale_grid_runs_width
REPORT_ROOT=backend/reports/scale_grid_width
TOKENS=backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy
# SFT/eval data: the K240 policy-only + coverage-fill set, so the W series doubles as the K240 column
# of the K_eff series (see config/keff_policies.json, tools/build_keff_datasets.py).
DATA=backend/models/compact_llm/datasets/keff_series/K240

# Freeze the preregistration: record the config hash next to the reports before anything trains.
mkdir -p "$REPORT_ROOT"
sha256sum "$CONFIG" "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl" | tee "$REPORT_ROOT/width_series.inputs.sha256"

exec "$PY" tools/run_scale_grid.py \
  --scale-config "$CONFIG" \
  --run-root "$RUN_ROOT" \
  --report-root "$REPORT_ROOT" \
  --tokens-npy "$TOKENS" \
  --subset-dir "$DATA" \
  --val-jsonl "$DATA/val.jsonl" \
  --dataset "$DATA/test_rule.jsonl" \
  --fractions 100 \
  --seeds 42 43 44 \
  --pretrain-steps 2400 \
  --sft-epochs 4 \
  --gpus 1 0 --max-parallel 2 \
  "$@"
