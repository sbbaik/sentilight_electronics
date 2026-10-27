#!/usr/bin/env bash
# E1(b): does a neutral context clause (no colour / emotion / intensity word) around an otherwise identical request
# hurt the 240-class head more than the decoder? Development-test rows (2,000) with a leading or trailing clause,
# both models, five seeds. Original-sentence results are the stored evaluation outputs.
set -euo pipefail
W="$(cd "$(dirname "$0")/.." && pwd)"; PY=/home/sbbaik/miniconda3/envs/sentilight/bin/python; OUT="$W/analysis/head_ablation"
TOK="$W/models/tokenizers/natural_corpus_V2/V4k"; export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
"$PY" - "$W" <<'PY'
import json, sys
from pathlib import Path
W = Path(sys.argv[1]); src = W / "data/datasets/K240_keff/test_rule.jsonl"; out = W / "analysis/head_ablation/datasets"
LEAD = "퇴근하고 집에 막 들어왔는데 짐 정리는 내일 하려고. "              # no policy vocabulary
TRAIL = " 그리고 내일 아침 회의 자료는 책상 위에 둘게."
LEAD2 = "오늘은 외근이 두 건이나 있어서 하루가 길었어. 저녁은 간단히 먹고 설거지까지 끝냈어. "   # longer, as in the audited context clauses
rows = [json.loads(l) for l in src.open(encoding="utf-8")]
for name, f in (("lead", lambda s: LEAD + s), ("trail", lambda s: s + TRAIL), ("lead_long", lambda s: LEAD2 + s)):
    with (out / f"dev_{name}.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({**r, "input": f(r["input"]), "source": f"dev_{name}"}, ensure_ascii=False) + "\n")
    print(name, len(rows), "rows written")
PY
cd "$W/code"
for v in lead trail lead_long; do
  D="$OUT/datasets/dev_$v.jsonl"
  for s in 42 43 44 45 46; do
    [[ -f "$OUT/per_row/head_${v}_s$s.jsonl" ]] || "$PY" "$W/tools/evaluate_head_checkpoint.py" --checkpoint "$W/models/head/clf_s$s.pt" --dataset "$D" --tokenizer-path "$TOK/tokenizer.json" \
        --model-id head_${v}_s$s --per-row-jsonl "$OUT/per_row/head_${v}_s$s.jsonl" --report-json "$OUT/per_row/head_${v}_s$s.json" > /dev/null 2>&1 &
  done; wait
  for s in 42 43 44 45 46; do
    [[ -f "$OUT/per_row/decoder_${v}_s$s.jsonl" ]] || "$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$W/models/doi_release/selected_d384_L8_V4k/fp32_seed$s.pt" --dataset "$D" --segment rule \
        --model-dir "$W/code/backend/models/compact_llm_q4" --tokenizer-dir "$TOK" --device cpu --model-id decoder_${v}_s$s --display-name x \
        --per-row-jsonl "$OUT/per_row/decoder_${v}_s$s.jsonl" --report-json "$OUT/per_row/decoder_${v}_s$s.json" --report-md "$OUT/per_row/decoder_${v}_s$s.md" > "$OUT/per_row/decoder_${v}_s$s.log" 2>&1 &
  done; wait
  echo "[done] $v $(date '+%T')"
done
echo "[all done]"
