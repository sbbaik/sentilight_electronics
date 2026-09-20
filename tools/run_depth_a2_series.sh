#!/usr/bin/env bash
# Attribute-count control: depth sweep at A = 2 (policy A2K192), reusing D-series pretrain checkpoints (d 384, V 24k).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/depth_series.json
DATA=backend/models/compact_llm/datasets/keff_series/A2K192
D_RUN_ROOT=backend/models/compact_llm/scale_grid_runs_depth
RUN_ROOT=backend/models/compact_llm/scale_grid_runs_depth_a2
REPORT_ROOT=backend/reports/scale_grid_depth_a2
mkdir -p "$REPORT_ROOT"
sha256sum config/depth_a2_series.json "$DATA/train_100.jsonl" "$DATA/val.jsonl" "$DATA/test_rule.jsonl" | tee "$REPORT_ROOT/inputs.sha256"
for S in D2 D4 D6 D8; do for s in 42 43 44; do
  SRC="$D_RUN_ROOT/$S/seed_$s/pretrain"; [[ -f "$SRC/compactlm_pretrain_best.pt" ]] || { echo "missing $SRC" >&2; exit 2; }
  mkdir -p "$RUN_ROOT/$S/seed_$s"; ln -sfn "$(realpath "$SRC")" "$RUN_ROOT/$S/seed_$s/pretrain"
done; done
exec "$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales D2 D4 D6 D8 \
  --run-root "$RUN_ROOT" --report-root "$REPORT_ROOT" \
  --tokens-npy backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy \
  --subset-dir "$DATA" --val-jsonl "$DATA/val.jsonl" --dataset "$DATA/test_rule.jsonl" \
  --fractions 100 --seeds 42 43 44 --sft-epochs 4 --gpus 1 0 --max-parallel 2 --phases sft eval "$@"
