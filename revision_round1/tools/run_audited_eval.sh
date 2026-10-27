#!/usr/bin/env bash
# Evaluate the audited request set (240 rows) on every model family the paper compares, inference only.
# CPU: no GPU driver on this host. Idempotent — an evaluation whose per-row file exists is skipped.
set -euo pipefail
W="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
CODE="$W/code"; DATA="$W/data/audited_requests/audited_requests_K240.jsonl"
OUT="$W/analysis/audited_eval"; mkdir -p "$OUT/per_row" "$OUT/run_summaries"
TOK4="$W/models/tokenizers/natural_corpus_V2/V4k"; TOK24="$W/models/tokenizers/production_24k"
MODEL_DIR="$CODE/backend/models/compact_llm"
cd "$CODE"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4   # the paper's four-thread condition; 24 threads oversubscribe a 15.7 M model
date '+%F %T' > "$OUT/launch_started_at.txt"; sha256sum "$DATA" > "$OUT/inputs.sha256"

gen() { # id ckpt tokdir
  [[ -f "$OUT/per_row/$1.jsonl" ]] && { echo "[skip] $1"; return 0; }
  "$PY" tools/evaluate_compactlm_checkpoint.py --checkpoint "$2" --dataset "$DATA" --segment rule \
    --model-dir "$MODEL_DIR" --tokenizer-dir "$3" --device cpu --model-id "$1" --display-name "$1 on audited set" \
    --per-row-jsonl "$OUT/per_row/$1.jsonl" --report-json "$OUT/run_summaries/$1.json" --report-md "$OUT/run_summaries/$1.md" \
    --progress-every 60 > "$OUT/run_summaries/$1.log" 2>&1 && echo "[ok] $1" || echo "[FAIL] $1"
}
quant() { # id ckpt tokdir  (the quantized loader takes the model class from its own directory)
  [[ -f "$OUT/per_row/$1.jsonl" ]] && { echo "[skip] $1"; return 0; }
  "$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$2" --dataset "$DATA" --segment rule \
    --model-dir "$CODE/backend/models/compact_llm_q4" --tokenizer-dir "$3" --device cpu --model-id "$1" --display-name "$1 on audited set" \
    --per-row-jsonl "$OUT/per_row/$1.jsonl" --report-json "$OUT/run_summaries/$1.json" --report-md "$OUT/run_summaries/$1.md" \
    > "$OUT/run_summaries/$1.log" 2>&1 && echo "[ok] $1" || echo "[FAIL] $1"
}
head_() { # id ckpt tokjson
  [[ -f "$OUT/per_row/$1.jsonl" ]] && { echo "[skip] $1"; return 0; }
  "$PY" "$W/tools/evaluate_head_checkpoint.py" --checkpoint "$2" --dataset "$DATA" --segment rule \
    --tokenizer-path "$3" --device cpu --model-id "$1" --display-name "$1 on audited set" \
    --per-row-jsonl "$OUT/per_row/$1.jsonl" --report-json "$OUT/run_summaries/$1.json" --report-md "$OUT/run_summaries/$1.md" \
    > "$OUT/run_summaries/$1.log" 2>&1 && echo "[ok] $1" || echo "[FAIL] $1"
}

# one family at a time, its five seeds in parallel (5 x 4 threads on 24 cores)
for s in 42 43 44 45 46; do gen   "selected_V4k_L8_s$s"        "$W/models/doi_release/selected_d384_L8_V4k/fp32_seed$s.pt"          "$TOK4" & done; wait
for s in 42 43 44 45 46; do quant "selected_V4k_L8_mixed4_s$s" "$W/models/doi_release/selected_d384_L8_V4k/mixed4_6_8bit_seed$s.pt" "$TOK4" & done; wait
for s in 42 43 44 45 46; do gen   "deployed_W384_L8_V24k_s$s"  "$W/models/reference_W384/fp32_seed$s.pt"                           "$TOK24" & done; wait
for s in 42 43 44 45 46; do head_ "head240_s$s"                "$W/models/head/clf_s$s.pt"                                          "$TOK4/tokenizer.json" & done; wait
date '+%F %T' > "$OUT/launch_finished_at.txt"; echo "[done]"
