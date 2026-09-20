#!/usr/bin/env bash
# L = 3 addition to the depth series: pretrain D3 (5 seeds) once, SFT+eval on K240 (A = 3) and on A2K192 (A = 2).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CONFIG=config/depth_l3_series.json
TOKENS=backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy
SEEDS="42 43 44 45 46"
A3_DATA=backend/models/compact_llm/datasets/keff_series/K240
A2_DATA=backend/models/compact_llm/datasets/keff_series/A2K192
A3_RUN=backend/models/compact_llm/scale_grid_runs_depth
A2_RUN=backend/models/compact_llm/scale_grid_runs_depth_a2
A3_REP=backend/reports/scale_grid_depth_l3
A2_REP=backend/reports/scale_grid_depth_a2_l3
mkdir -p "$A3_REP" "$A2_REP"
sha256sum "$CONFIG" "$A3_DATA"/{train_100,val,test_rule}.jsonl "$A2_DATA"/{train_100,val,test_rule}.jsonl | tee "$A3_REP/inputs.sha256" > "$A2_REP/inputs.sha256"
date '+%F %T' > "$A3_REP/launch_started_at.txt"

echo "[A=3] pretrain -> sft -> eval on K240"
"$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales D3 \
  --run-root "$A3_RUN" --report-root "$A3_REP" --tokens-npy "$TOKENS" \
  --subset-dir "$A3_DATA" --val-jsonl "$A3_DATA/val.jsonl" --dataset "$A3_DATA/test_rule.jsonl" \
  --fractions 100 --seeds $SEEDS --pretrain-steps 2400 --sft-epochs 4 --gpus 1 0 --max-parallel 2 "$@"

echo "[A=2] link D3 pretrain, sft -> eval on A2K192"
for s in $SEEDS; do
  SRC="$A3_RUN/D3/seed_$s/pretrain"; [[ -f "$SRC/compactlm_pretrain_best.pt" ]] || { echo "missing $SRC" >&2; exit 2; }
  mkdir -p "$A2_RUN/D3/seed_$s"; ln -sfn "$(realpath "$SRC")" "$A2_RUN/D3/seed_$s/pretrain"
done
"$PY" tools/run_scale_grid.py --scale-config "$CONFIG" --scales D3 \
  --run-root "$A2_RUN" --report-root "$A2_REP" --tokens-npy "$TOKENS" \
  --subset-dir "$A2_DATA" --val-jsonl "$A2_DATA/val.jsonl" --dataset "$A2_DATA/test_rule.jsonl" \
  --fractions 100 --seeds $SEEDS --sft-epochs 4 --gpus 1 0 --max-parallel 2 --phases sft eval "$@"
date '+%F %T' > "$A3_REP/launch_finished_at.txt"
echo "[done]"
