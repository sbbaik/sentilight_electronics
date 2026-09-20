#!/usr/bin/env bash
# K_eff series: for each nested policy train the width grid on that policy's own SFT data and
# evaluate on its own rule test set. Pretraining is policy-independent, so the W-series pretrain
# checkpoints (scale_grid_runs_width/<scale>/seed_<s>/pretrain) are linked into each policy's
# run root and only the SFT + eval phases run.
#
# K240 is NOT run here: the W series (tools/run_width_series.sh) already trains on the K240 data
# and is the K_eff = 240 column of this series.
#
# Prerequisites: python tools/build_keff_datasets.py ; tools/run_width_series.sh finished.
# Usage:
#   tools/run_keff_series.sh --dry-run
#   tools/run_keff_series.sh                         # K48 K480 K960, d in {128,192,256,384,512}
#   POLICIES="K48" tools/run_keff_series.sh
#   tools/run_keff_series.sh --phases eval
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
POLICIES="${POLICIES:-K48 K480 K960}"
SCALES="${SCALES:-W128 W192 W256 W384 W512}"
SEEDS="${SEEDS:-42 43 44}"
CONFIG=config/width_series.json
DATA_ROOT=backend/models/compact_llm/datasets/keff_series
W_RUN_ROOT=backend/models/compact_llm/scale_grid_runs_width
TOKENS=backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy

for P in $POLICIES; do
  RUN_ROOT=${RUN_BASE:-backend/models/compact_llm/scale_grid_runs_keff}/$P
  REPORT_ROOT=${REPORT_BASE:-backend/reports/scale_grid_keff}/$P
  mkdir -p "$REPORT_ROOT"
  sha256sum "$CONFIG" "$DATA_ROOT/$P/train_100.jsonl" "$DATA_ROOT/$P/val.jsonl" "$DATA_ROOT/$P/test_rule.jsonl" \
    | tee "$REPORT_ROOT/inputs.sha256"
  # link W-series pretrain checkpoints (status.json = done makes the runner skip pretraining)
  for S in $SCALES; do
    for s in $SEEDS; do
      SRC="$W_RUN_ROOT/$S/seed_$s/pretrain"
      if [[ ! -f "$SRC/compactlm_pretrain_best.pt" ]]; then
        echo "missing W pretrain checkpoint: $SRC" >&2; exit 2
      fi
      mkdir -p "$RUN_ROOT/$S/seed_$s"
      ln -sfn "$(realpath "$SRC")" "$RUN_ROOT/$S/seed_$s/pretrain"
    done
  done
  "$PY" tools/run_scale_grid.py \
    --scale-config "$CONFIG" --scales $SCALES \
    --run-root "$RUN_ROOT" --report-root "$REPORT_ROOT" \
    --tokens-npy "$TOKENS" \
    --subset-dir "$DATA_ROOT/$P" \
    --val-jsonl "$DATA_ROOT/$P/val.jsonl" \
    --dataset "$DATA_ROOT/$P/test_rule.jsonl" \
    --fractions 100 --seeds $SEEDS \
    --pretrain-steps 2400 --sft-epochs 4 \
    --gpus 1 0 --max-parallel 2 \
    --phases sft eval \
    "$@"
done
