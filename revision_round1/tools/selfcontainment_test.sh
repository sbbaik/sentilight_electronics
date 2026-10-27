#!/usr/bin/env bash
# Self-containment test for the v1.1.0 addition: in a scratch copy that holds ONLY the v1.0.0 package files the
# scripts need plus revision_round1/, rebuild the inputs, re-run every analysis, and compare with the staged outputs.
# A short inference smoke (one seed per family, 12 rows) checks that the evaluators run from the package and
# reproduce the released predictions row for row. The full 20-evaluation re-run is left to run_audited_eval.sh.
set -euo pipefail
W="$(cd "$(dirname "$0")/.." && pwd)"
PKG="${PKG:-$W/../MDPI_Electronics_submitted_1st/sentilight_electronics}"
T="${T:-${TMPDIR:-/tmp}/sentilight_selfcontain}"
PY="${PY:-/home/sbbaik/miniconda3/envs/sentilight/bin/python}"
rm -rf "$T"; mkdir -p "$T/evaluation_outputs" "$T/datasets" "$T/tokenizers" "$T/models" "$T/tables"
for f in scale_grid_vocab_natural holdout_final holdout_paraphrase baselines_nongenerative; do cp "$PKG/evaluation_outputs/$f.tar.gz" "$T/evaluation_outputs/"; done
for f in keff_series holdout_unseen_frames holdout_paraphrase; do cp "$PKG/datasets/$f.tar.gz" "$T/datasets/"; done
cp "$PKG"/tokenizers/*.tar.gz "$T/tokenizers/"; cp "$PKG"/tables/*.csv "$T/tables/"
cp -r "$PKG/models/selected_d384_L8_V4k" "$T/models/"
cp -r "$W/release_v1.1.0/revision_round1" "$T/revision_round1"
R="$T/revision_round1"
# the staged analysis outputs are the reference; the re-run must reproduce them
mv "$R/analysis" "$T/analysis_released"; mkdir -p "$R/analysis/audited_eval"; cp -r "$T/analysis_released/audited_eval/per_row" "$R/analysis/audited_eval/"
mkdir -p "$R/analysis/head_ablation"; cp -r "$T/analysis_released/head_ablation/per_row" "$T/analysis_released/head_ablation/datasets" "$R/analysis/head_ablation/"
for d in "" draw2 draw3; do
  mkdir -p "$R/analysis/random_subsets/$d"; cp -r "$T/analysis_released/random_subsets/$d/per_row" "$T/analysis_released/random_subsets/$d/run_summaries" "$R/analysis/random_subsets/$d/"
done
mv "$R/figures" "$T/figures_released"; mkdir -p "$R/figures"
bash "$R/prepare_inputs.sh"
cd "$R"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
for s in analyze_per_action_exposure analyze_depth_pareto analyze_search_counterfactual simulate_generic_search build_random_subset_policies analyze_random_subsets make_common_k48_figure make_quant_boundary_table analyze_audited_requests analyze_head_reversal; do
  echo "== $s"; "$PY" "tools/$s.py" > "$T/sc_$s.log" 2>&1 || { echo "[FAIL] $s"; tail -5 "$T/sc_$s.log"; exit 1; }
done
echo "== compare JSON/MD/CSV outputs with the released ones"
fail=0
while IFS= read -r f; do
  rel="${f#$T/analysis_released/}"
  if [[ "$rel" == audited_eval/* || "$rel" == e2e_simulated/* || "$rel" == random_subsets/run_summaries/* || "$rel" == random_subsets/draw*/run_summaries/* ]]; then continue; fi
  if ! cmp -s "$f" "$R/analysis/$rel"; then echo "  DIFF analysis/$rel"; fail=1; fi
done < <(find "$T/analysis_released" -type f \( -name "*.json" -o -name "*.md" -o -name "*.csv" \))
for f in "$T"/figures_released/*.json; do cmp -s "$f" "$R/figures/$(basename "$f")" || { echo "  DIFF figures/$(basename "$f")"; fail=1; }; done
[[ $fail == 0 ]] && echo "  all analysis outputs identical"
echo "== inference smoke from the package (12 rows, seed 42, three evaluators)"
D="$R/data/audited_requests/audited_requests_K240.jsonl"; S="$T/smoke"; mkdir -p "$S"; cd "$R/code"
"$PY" tools/evaluate_compactlm_checkpoint.py --checkpoint "$R/models/doi_release/selected_d384_L8_V4k/fp32_seed42.pt" --dataset "$D" --segment rule --device cpu \
  --model-dir "$R/code/backend/models/compact_llm" --tokenizer-dir "$R/models/tokenizers/natural_corpus_V2/V4k" --model-id sel --display-name sel --max-rows 12 \
  --per-row-jsonl "$S/sel.jsonl" --report-json "$S/sel.json" --report-md "$S/sel.md" --progress-every 100 > "$S/sel.log" 2>&1
"$PY" tools/evaluate_quantized_checkpoint.py --checkpoint "$R/models/doi_release/selected_d384_L8_V4k/mixed4_6_8bit_seed42.pt" --dataset "$D" --segment rule --device cpu \
  --model-dir "$R/code/backend/models/compact_llm_q4" --tokenizer-dir "$R/models/tokenizers/natural_corpus_V2/V4k" --model-id mix --display-name mix --max-rows 12 \
  --per-row-jsonl "$S/mix.jsonl" --report-json "$S/mix.json" --report-md "$S/mix.md" > "$S/mix.log" 2>&1
"$PY" "$R/tools/evaluate_head_checkpoint.py" --checkpoint "$R/models/head/clf_s42.pt" --dataset "$D" --tokenizer-path "$R/models/tokenizers/natural_corpus_V2/V4k/tokenizer.json" \
  --model-id head --max-rows 12 --per-row-jsonl "$S/head.jsonl" --report-json "$S/head.json" > "$S/head.log" 2>&1
"$PY" - "$S" "$T/analysis_released/audited_eval/per_row" <<'EOF'
import json, sys
from pathlib import Path
S, REL = Path(sys.argv[1]), Path(sys.argv[2])
ok = True
for smoke, released in (("sel.jsonl", "selected_V4k_L8_s42.jsonl"), ("mix.jsonl", "selected_V4k_L8_mixed4_s42.jsonl"), ("head.jsonl", "head240_s42.jsonl")):
    a = [json.loads(l) for l in (S / smoke).open(encoding="utf-8")]
    b = {r["input"]: r for r in (json.loads(l) for l in (REL / released).open(encoding="utf-8"))}
    same = sum(r["predicted"] == b[r["input"]]["predicted"] for r in a)
    print(f"  {smoke}: {same}/{len(a)} predictions identical to the released per-row file")
    ok &= same == len(a)
print("  smoke identical" if ok else "  SMOKE MISMATCH"); sys.exit(0 if ok else 1)
EOF
echo "== self-containment test finished"
