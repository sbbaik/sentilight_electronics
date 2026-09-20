#!/usr/bin/env bash
# Evaluation-only pass of the five-seed CompactLM configurations on the paraphrase hold-out.
set -euo pipefail; cd "$(dirname "$0")/.."
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
DATA=backend/models/compact_llm/datasets/holdout_paraphrase/K240/holdout_paraphrase.jsonl
M=backend/models/compact_llm; OUT=backend/reports/holdout_paraphrase; mkdir -p "$OUT/per_row" "$OUT/run_summaries"
TOK24=$(realpath $M/tokenizer); TOK4=$(realpath $M/tokenizer_vocab_series_natural/V4k)
date '+%F %T' > "$OUT/launch_started_at.txt"; sha256sum "$DATA" > "$OUT/inputs.sha256"
jobs=()
add() { [[ -f "$2" ]] || { echo "missing $2" >&2; return 0; }; [[ -f "$OUT/per_row/$1.jsonl" ]] && return 0; jobs+=("$1|$2|$3"); }
for s in 42 43 44 45 46; do
  add "selected_V4k_L8_s$s"  "$M/scale_grid_runs_vocab_natural/V4k/V4k/seed_$s/f100/sft/compactlm_from_scratch_best.pt" "$TOK4"
  add "deployed_W384_L8_V24k_s$s" "$M/scale_grid_runs_width/W384/seed_$s/f100/sft/compactlm_from_scratch_best.pt" "$TOK24"
  add "X320_V4k_s$s" "$M/scale_grid_runs_width_v4k/X320/seed_$s/f100/sft/compactlm_from_scratch_best.pt" "$TOK4"
done
echo "[plan] ${#jobs[@]} evaluations"
i=0
for j in "${jobs[@]}"; do IFS='|' read -r id ck tok <<< "$j"; gpu=$((i % 2)); i=$((i+1))
  ( CUDA_VISIBLE_DEVICES=$gpu "$PY" tools/evaluate_compactlm_checkpoint.py --checkpoint "$ck" --dataset "$DATA" --segment rule --tokenizer-dir "$tok" --device cuda:0 \
      --model-id "$id" --display-name "$id on paraphrase holdout" --per-row-jsonl "$OUT/per_row/$id.jsonl" --report-json "$OUT/run_summaries/$id.json" --report-md "$OUT/run_summaries/$id.md" --progress-every 500 \
      > "$OUT/run_summaries/$id.log" 2>&1 && echo "[ok] $id" || echo "[FAIL] $id" ) &
  if (( i % 2 == 0 )); then wait; fi
done; wait
for s in 42 43 44 45 46; do
  q="$M/scale_grid_runs_vocab_natural_q4/V4k_s${s}_mixed4.pt"; id="selected_V4k_L8_mixed4_s$s"
  [[ -f "$q" && ! -f "$OUT/per_row/$id.jsonl" ]] || continue
  CUDA_VISIBLE_DEVICES=$(( s % 2 )) "$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$q" --dataset "$DATA" --tokenizer-dir "$TOK4" \
      --per-row-jsonl "$OUT/per_row/$id.jsonl" --report-json "$OUT/run_summaries/$id.json" --report-md "$OUT/run_summaries/$id.md" --device cuda:0 --model-id "$id" --display-name "$id on paraphrase holdout" > "$OUT/run_summaries/$id.log" 2>&1 && echo "[ok] $id" || echo "[FAIL] $id (see log)"
done
date '+%F %T' > "$OUT/launch_finished_at.txt"; echo "[done]"
