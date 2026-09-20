#!/usr/bin/env bash
# Evaluate every K-series model at d in {256,384} (both SFT budgets, all available seeds) on ONE fixed test set:
# the K48 policy's 2,000-row test_rule. Evaluation only; no training. Two GPUs, 2 jobs in parallel.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
DATA=backend/models/compact_llm/datasets/keff_series/K48/test_rule.jsonl
TOK=$(realpath backend/models/compact_llm/tokenizer)
OUT=backend/reports/scale_grid_keff_common48; mkdir -p "$OUT"
date '+%F %T' > "$OUT/launch_started_at.txt"
jobs=()
add() { # cond policy runroot d seed
  local ck="$3/W$4/seed_$5/f100/sft/compactlm_from_scratch_best.pt"; [[ -f "$ck" ]] || return 0
  local id="${2}_W$4_s$5"; mkdir -p "$OUT/$1/per_row" "$OUT/$1/run_summaries"
  [[ -f "$OUT/$1/per_row/$id.jsonl" ]] && return 0
  jobs+=("$ck|$1|$id"); }
for d in 256 384; do for s in 42 43 44 45 46; do
  add fixed_steps K48  backend/models/compact_llm/scale_grid_runs_keff_fs/K48  $d $s
  add fixed_steps K240 backend/models/compact_llm/scale_grid_runs_width          $d $s
  add fixed_steps K480 backend/models/compact_llm/scale_grid_runs_keff_fs/K480 $d $s
  add fixed_steps K960 backend/models/compact_llm/scale_grid_runs_keff_fs/K960 $d $s
  add fixed_epochs K48  backend/models/compact_llm/scale_grid_runs_keff/K48  $d $s
  add fixed_epochs K480 backend/models/compact_llm/scale_grid_runs_keff/K480 $d $s
  add fixed_epochs K960 backend/models/compact_llm/scale_grid_runs_keff/K960 $d $s
done; done
echo "[plan] ${#jobs[@]} evaluations"
[[ "${1:-}" == "--dry-run" ]] && { printf '%s\n' "${jobs[@]}"; exit 0; }
i=0
for j in "${jobs[@]}"; do
  IFS='|' read -r ck cond id <<< "$j"; gpu=$((i % 2)); i=$((i+1))
  ( CUDA_VISIBLE_DEVICES=$gpu "$PY" tools/evaluate_compactlm_checkpoint.py --checkpoint "$ck" --dataset "$DATA" --segment rule \
      --tokenizer-dir "$TOK" --device cuda:0 --model-id "$id" --display-name "$id on K48 test" \
      --per-row-jsonl "$OUT/$cond/per_row/$id.jsonl" --report-json "$OUT/$cond/run_summaries/$id.json" --report-md "$OUT/$cond/run_summaries/$id.md" \
      --progress-every 500 > "$OUT/$cond/run_summaries/$id.log" 2>&1 && echo "[ok] $cond $id" || echo "[FAIL] $cond $id" ) &
  if (( i % 2 == 0 )); then wait; fi
done; wait
date '+%F %T' > "$OUT/launch_finished_at.txt"; echo "[done]"
