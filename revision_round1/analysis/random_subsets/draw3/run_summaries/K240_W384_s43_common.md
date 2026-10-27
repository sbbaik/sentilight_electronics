# CompactLM Direct Checkpoint Evaluation

- Model: `K240_W384_s43_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/Implement_New_Android_v6/backend/models/compact_llm/scale_grid_runs_width/W384/seed_43/f100/sft/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw3/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `400`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/per_row/K240_W384_s43_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 400/400 | 202 (50.50%) | 343 (85.75%) | 210.98 | 250.93 |
