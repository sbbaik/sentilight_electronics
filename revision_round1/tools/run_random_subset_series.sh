#!/usr/bin/env bash
# E2 — random-subset policies with fixed semantic composition (R1-1, R2-1). GPU launcher.
#
# Policies K48r / K96r / K144r are nested random subsets of the 240 production cells (tools/build_random_subset_policies.py);
# their training rows are the K240 rows of the kept cells, so exposure per action is the K240 exposure. Two schedules,
# as in the K series: matched exposure (4 epochs for every policy) and fixed steps (epochs scaled so that every policy
# sees the K240 step count, 4 × 49,093 / 64 ≈ 3,070 steps: K48r 20, K96r 10, K144r 7 epochs). Widths d ∈ {256, 384},
# seeds 42–44, pretraining = the W-series pretraining checkpoints of the original grid (24k production tokenizer; not in the v1.0.0 record), SFT recipe unchanged
# (batch 64, lr 1e-4, wd 0.01, warmup 5 %, max_seq_len 256). Evaluation on the policy's own test rows and on the
# common K48r test (gold identical for every superset policy).
#
# Needs a CUDA device (the fine-tuning script is the original one). On CPU the same commands run with
# finetune_from_pretrain_cpu.py --devices cpu, but at ~10–20 s per step this is a multi-day job.
# Usage: tools/run_random_subset_series.sh [--dry-run]        env: SEEDS, WIDTHS, POLICIES, SCHEDULES, DEVICES, PY, DATA, OUT
# Further draws: DATA=data/datasets/random_subsets/draw2 OUT=analysis/random_subsets/draw2 WIDTHS=384 SEEDS='42 43 44 45 46'
set -euo pipefail
W="$(cd "$(dirname "$0")/.." && pwd)"; A="${APP:-$HOME/Sentilight_Paper_2/Implement_New_Android_v6}"
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
SEEDS="${SEEDS:-42 43 44}"; WIDTHS="${WIDTHS:-256 384}"; POLICIES="${POLICIES:-K48r K96r K144r}"; SCHEDULES="${SCHEDULES:-matched fixed}"
DEVICES="${DEVICES:-0}"; DRY=0; [[ "${1:-}" == "--dry-run" ]] && DRY=1
TOK="$W/models/tokenizers/production_24k/tokenizer.json"; DATA="${DATA:-$W/data/datasets/random_subsets}"; OUT="${OUT:-$W/analysis/random_subsets}"
declare -A FIXED_EPOCHS=([K48r]=20 [K96r]=10 [K144r]=7)
mkdir -p "$OUT/runs" "$OUT/per_row" "$OUT/run_summaries"
if [[ "$DEVICES" == cpu ]]; then FT="$W/code/backend/models/compact_llm/finetune_from_pretrain_cpu.py"; else FT="$A/backend/models/compact_llm/finetune_from_pretrain.py"; fi
date '+%F %T %Z' > "$OUT/launch_started_at.txt"; sha256sum "$DATA"/*/train_100.jsonl "$DATA"/common_test_K48r.jsonl > "$OUT/inputs.sha256"
n=0
for P in $POLICIES; do for S in $SCHEDULES; do for d in $WIDTHS; do for s in $SEEDS; do
  if [[ "$S" == matched ]]; then EP=4; else EP=${FIXED_EPOCHS[$P]}; fi
  id="${P}_${S}_W${d}_s${s}"; run="$OUT/runs/$id"; ck="$run/compactlm_from_scratch_best.pt"
  pre="$A/backend/models/compact_llm/scale_grid_runs_width/W${d}/seed_${s}/pretrain/compactlm_pretrain_best.pt"
  [[ -f "$pre" ]] || { echo "missing pretrain checkpoint $pre" >&2; exit 2; }
  n=$((n+1))
  if [[ $DRY == 1 ]]; then echo "[dry] $id epochs=$EP pretrain=$(basename "$(dirname "$(dirname "$pre")")")/$(basename "$(dirname "$pre")")"; continue; fi
  if [[ ! -f "$ck" ]]; then
    echo "[sft] $id epochs=$EP $(date '+%T')"
    ( cd "$A" && "$PY" "$FT" --train-jsonl "$DATA/$P/train_100.jsonl" --val-jsonl "$DATA/$P/val.jsonl" --pretrained-checkpoint "$pre" \
        --tokenizer-path "$TOK" --output-dir "$run" --epochs "$EP" --batch-size 64 --learning-rate 1e-4 --seed "$s" --devices "$DEVICES" --max-seq-len 256 ) > "$run.log" 2>&1 || { echo "[FAIL sft] $id"; continue; }
  fi
  for T in own common; do
    if [[ $T == own ]]; then DS="$DATA/$P/test_rule.jsonl"; else DS="$DATA/common_test_K48r.jsonl"; fi
    [[ -f "$OUT/per_row/${id}_${T}.jsonl" ]] && continue
    ( cd "$W/code" && OMP_NUM_THREADS=4 "$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$ck" --dataset "$DS" --segment rule --device cpu \
        --model-dir "$W/code/backend/models/compact_llm_q4" --tokenizer-dir "$W/models/tokenizers/production_24k" --model-id "${id}_${T}" --display-name "${id}_${T}" \
        --per-row-jsonl "$OUT/per_row/${id}_${T}.jsonl" --report-json "$OUT/run_summaries/${id}_${T}.json" --report-md "$OUT/run_summaries/${id}_${T}.md" ) > "$OUT/run_summaries/${id}_${T}.log" 2>&1 || echo "[FAIL eval] $id $T"
  done
done; done; done; done
echo "[done] $n runs $(date '+%F %T %Z')"; date '+%F %T %Z' > "$OUT/launch_finished_at.txt"
