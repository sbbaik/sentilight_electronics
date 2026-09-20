# Production rule-1000 benchmark: inputs with conflicting gold tuples

- Found: 2026-09-04 while porting the v3 benchmark templates to the K_eff series generator
- Data: `backend/reports/benchmark_datasets/v3_test_mixed_2000.jsonl`, rule segment (source != natural_language_baseline)
- Per-row predictions: `backend/reports/five_model_benchmark_v3_per_row.jsonl` (2026-08-01 rerun)

## What is wrong

`scripts/create_v3_benchmark_dataset.py` builds emotion-only holdout rows and ambiguous-fallback rows
by looping over all five intensities and calling `resolve_case_output({... "intensity": i})`, but the
text templates for those two groups contain no intensity word. The same sentence is therefore emitted
up to five times with five different reference tuples. The dedupe key (input, emotion, base_color,
intensity) treats them as distinct rows.

| Quantity | Value |
|---|---:|
| Rule-1000 inputs carrying more than one distinct gold tuple | 34 |
| Rows affected | 105 / 1,000 |
| … of which `ambiguous_fallback_cases` | 94 / 100 |
| … of which `color_emotion_intensity_combinations` | 11 / 700 |
| `conflict_and_color_adjective_cases` affected | 0 / 200 |

Example (four gold tuples for one sentence):

```
"과하지 않게 적당한 느낌이면 돼. 너무 튀지 않게 부탁해"
  -> (42,0,48,44,318)  (43,12,26,24,338)  (46,24,72,72,292)  (47,30,64,64,290)
```

## Effect on reported numbers

These rows are unanswerable from the text; a model can match at most one of the gold tuples.

| Model | 105 ambiguous rows: strict / coarse | 895 unambiguous rows: strict / coarse |
|---|---:|---:|
| compact_llm_q4 | 12.4% / 7.6% | 40.8% / 69.1% |
| compact_llm (FP32) | 12.4% / 7.6% | 39.7% / 68.2% |
| qwen3_0.6B | 7.6% / 1.9% | 35.0% / 45.4% |
| gemini_api | 0.0% / 2.9% | 6.0% / 17.1% |
| sbert | 2.9% / 1.0% | 4.9% / 11.4% |

Consequences:

1. The "unseen tuple" effect reported earlier (19 policy tuples absent from training, 108 rows, ~8%
   coarse) is almost entirely this defect, not a generalisation failure: those tuples are
   (emotion-only, non-neutral intensity) and (fallback, non-neutral intensity), which the production
   generator never emits *and* the benchmark asks for without naming the intensity.
2. The IoTJ manuscript's Section VI-G statement that the action-head advantage "disappears on the 100
   fallback examples" is confounded: 94 of those 100 rows have no unique answer. The direction of
   C1 on that layer cannot be interpreted.
3. Headline rule-1000 numbers are depressed by roughly 10 percentage points of unanswerable rows for
   every model; relative comparisons between models are unaffected in sign.

## What the K_eff series does instead

`tools/build_keff_datasets.py`:

- Test: for non-neutral intensity, emotion-only and fallback rows use templates that name the
  intensity (`HOLDOUT_EMOTION_ONLY_INTENSITY`, `FALLBACK_TEMPLATES_INTENSITY`). The generator asserts
  that no test input carries more than one gold tuple.
- Train: adds `coverage_fill` rows for the same two lattice regions (templates disjoint from the
  test ones), so every reachable tuple is trained (production: 219/240). `--no-coverage-fill`
  reproduces the production generator exactly.
- Sampling guarantees at least `--min-per-tuple` (default 2) test rows per reachable tuple.

## Recommended follow-up for the production benchmark

Re-score the existing per-row predictions on the 895 unambiguous rows and report both numbers, or
regenerate rule-1000 with the intensity-aware templates and re-run the five models. Either way the
fallback-layer claim should be withdrawn or restated.
