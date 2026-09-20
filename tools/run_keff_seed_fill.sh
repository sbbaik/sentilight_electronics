#!/usr/bin/env bash
# K-series seed fill (seeds 45, 46). Phase A: width series W128/W512 (pretrain+SFT+eval, K240 data) — supplies pretrain for d128/d512.
# Phase B: fixed epochs K480/K960 at W384/W512. Phase C: fixed steps K48 W128/W192 (21 ep), K480 W192/W256 (2 ep), K960 W256/W384 (1 ep).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/width_series.json
TOKENS=backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy
DATA_ROOT=backend/models/compact_llm/datasets/keff_series
W_RUN=backend/models/compact_llm/scale_grid_runs_width
SEEDS="45 46"
LOG=backend/reports/scale_grid_keff_fill; mkdir -p "$LOG"
sha256sum config/keff_seed_fill.json "$CONFIG" | tee "$LOG/inputs.sha256"; date '+%F %T' > "$LOG/launch_started_at.txt"

echo "[A] width series W128 W512 seeds 45 46 (K240 data): pretrain -> sft -> eval"
"$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales W128 W512 \
  --run-root "$W_RUN" --report-root backend/reports/scale_grid_width --tokens-npy "$TOKENS" \
  --subset-dir "$DATA_ROOT/K240" --val-jsonl "$DATA_ROOT/K240/val.jsonl" --dataset "$DATA_ROOT/K240/test_rule.jsonl" \
  --fractions 100 --seeds $SEEDS --pretrain-steps 2400 --sft-epochs 4 --gpus 1 0 --max-parallel 2 "$@"

link() { # policy-run-root scale
  for s in $SEEDS; do SRC="$W_RUN/$2/seed_$s/pretrain"; [[ -f "$SRC/compactlm_pretrain_best.pt" ]] || { echo "missing $SRC" >&2; exit 2; }
    mkdir -p "$1/$2/seed_$s"; ln -sfn "$(realpath "$SRC")" "$1/$2/seed_$s/pretrain"; done; }
run_policy() { # base_run base_rep policy epochs scales...
  local RUN=$1/$3 REP=$2/$3 P=$3 EP=$4; shift 4
  for S in "$@"; do link "$RUN" "$S"; done
  "$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales "$@" \
    --run-root "$RUN" --report-root "$REP" --tokens-npy "$TOKENS" \
    --subset-dir "$DATA_ROOT/$P" --val-jsonl "$DATA_ROOT/$P/val.jsonl" --dataset "$DATA_ROOT/$P/test_rule.jsonl" \
    --fractions 100 --seeds $SEEDS --sft-epochs "$EP" --gpus 1 0 --max-parallel 2 --phases sft eval; }

echo "[B] fixed epochs (4): K480 W384 W512; K960 W384 W512"
run_policy backend/models/compact_llm/scale_grid_runs_keff backend/reports/scale_grid_keff K480 4 W384 W512
run_policy backend/models/compact_llm/scale_grid_runs_keff backend/reports/scale_grid_keff K960 4 W384 W512
echo "[C] fixed steps: K48 W128 W192 (21 ep); K480 W192 W256 (2 ep); K960 W256 W384 (1 ep)"
run_policy backend/models/compact_llm/scale_grid_runs_keff_fs backend/reports/scale_grid_keff_fs K48 21 W128 W192
run_policy backend/models/compact_llm/scale_grid_runs_keff_fs backend/reports/scale_grid_keff_fs K480 2 W192 W256
run_policy backend/models/compact_llm/scale_grid_runs_keff_fs backend/reports/scale_grid_keff_fs K960 1 W256 W384
date '+%F %T' > "$LOG/launch_finished_at.txt"; echo "[done]"
