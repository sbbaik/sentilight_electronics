#!/usr/bin/env bash
# Seed fill (45, 46) for A=3 L2, A=2 L2, A=2 L4. 2 pretrain + 6 SFT + 6 eval = 14 runs.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
TOKENS=backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_tokens.npy
A3_DATA=backend/models/compact_llm/datasets/keff_series/K240
A2_DATA=backend/models/compact_llm/datasets/keff_series/A2K192
A3_RUN=backend/models/compact_llm/scale_grid_runs_depth
A2_RUN=backend/models/compact_llm/scale_grid_runs_depth_a2
A3_REP=backend/reports/scale_grid_depth
A2_REP=backend/reports/scale_grid_depth_a2
LOGDIR=backend/reports/scale_grid_depth_fill; mkdir -p "$LOGDIR"
sha256sum config/depth_seed_fill.json config/depth_series.json | tee "$LOGDIR/inputs.sha256"
date '+%F %T' > "$LOGDIR/launch_started_at.txt"
echo "[A=3] D2 seeds 45 46: pretrain -> sft -> eval on K240"
"$PY" tools/run_scale_grid.py --scale-config config/depth_series.json --scales D2 \
  --run-root "$A3_RUN" --report-root "$A3_REP" --tokens-npy "$TOKENS" \
  --subset-dir "$A3_DATA" --val-jsonl "$A3_DATA/val.jsonl" --dataset "$A3_DATA/test_rule.jsonl" \
  --fractions 100 --seeds 45 46 --pretrain-steps 2400 --sft-epochs 4 --gpus 1 0 --max-parallel 2 "$@"
echo "[A=2] link D2/D4 pretrain seeds 45 46, sft -> eval on A2K192"
for S in D2 D4; do for s in 45 46; do
  SRC="$A3_RUN/$S/seed_$s/pretrain"; [[ -f "$SRC/compactlm_pretrain_best.pt" ]] || { echo "missing $SRC" >&2; exit 2; }
  mkdir -p "$A2_RUN/$S/seed_$s"; ln -sfn "$(realpath "$SRC")" "$A2_RUN/$S/seed_$s/pretrain"
done; done
"$PY" tools/run_scale_grid.py --scale-config config/depth_series.json --scales D2 D4 \
  --run-root "$A2_RUN" --report-root "$A2_REP" --tokens-npy "$TOKENS" \
  --subset-dir "$A2_DATA" --val-jsonl "$A2_DATA/val.jsonl" --dataset "$A2_DATA/test_rule.jsonl" \
  --fractions 100 --seeds 45 46 --sft-epochs 4 --gpus 1 0 --max-parallel 2 --phases sft eval "$@"
date '+%F %T' > "$LOGDIR/launch_finished_at.txt"
echo "[done]"
