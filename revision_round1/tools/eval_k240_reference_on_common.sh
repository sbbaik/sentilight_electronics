#!/usr/bin/env bash
# E2 reference point: the K240 (W-series, 4 epochs = fixed-step and matched schedule alike) checkpoints at d = 256 / 384,
# seeds 42–44, scored on the common K48r test and on the K48r/K96r/K144r own tests (subsets of the K240 test rows).
set -euo pipefail
W="$(cd "$(dirname "$0")/.." && pwd)"; A="${APP:-$HOME/Sentilight_Paper_2/Implement_New_Android_v6}"; PY=/home/sbbaik/miniconda3/envs/sentilight/bin/python
DATA="${DATA:-$W/data/datasets/random_subsets}"; OUT="${OUT:-$W/analysis/random_subsets}"; WIDTHS="${WIDTHS:-256 384}"; mkdir -p "$OUT/per_row" "$OUT/run_summaries"
for d in $WIDTHS; do for s in 42 43 44 45 46; do
  ck="$A/backend/models/compact_llm/scale_grid_runs_width/W${d}/seed_${s}/f100/sft/compactlm_from_scratch_best.pt"
  [[ -f "$ck" ]] || { echo "missing $ck"; continue; }
  for T in common K48r K96r K144r; do
    if [[ $T == common ]]; then DS="$DATA/common_test_K48r.jsonl"; else DS="$DATA/$T/test_rule.jsonl"; fi
    id="K240_W${d}_s${s}_${T}"; [[ -f "$OUT/per_row/$id.jsonl" ]] && continue
    ( cd "$W/code" && OMP_NUM_THREADS=4 "$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$ck" --dataset "$DS" --segment rule --device cpu \
        --model-dir "$W/code/backend/models/compact_llm_q4" --tokenizer-dir "$W/models/tokenizers/production_24k" --model-id "$id" --display-name "$id" \
        --per-row-jsonl "$OUT/per_row/$id.jsonl" --report-json "$OUT/run_summaries/$id.json" --report-md "$OUT/run_summaries/$id.md" ) > "$OUT/run_summaries/$id.log" 2>&1 && echo "[ok] $id" || echo "[FAIL] $id"
  done
done; done
