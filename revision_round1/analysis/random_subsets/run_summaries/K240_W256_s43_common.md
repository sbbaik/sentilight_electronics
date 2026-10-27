# CompactLM Direct Checkpoint Evaluation

- Model: `K240_W256_s43_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/Implement_New_Android_v6/backend/models/compact_llm/scale_grid_runs_width/W256/seed_43/f100/sft/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `369`
- Parameters: `12374272`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/per_row/K240_W256_s43_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 369/369 | 192 (52.03%) | 336 (91.06%) | 78.52 | 82.9 |
