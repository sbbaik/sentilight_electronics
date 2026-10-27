# CompactLM Direct Checkpoint Evaluation

- Model: `K144r_fixed_W384_s45_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/runs/K144r_fixed_W384_s45/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw3/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `400`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/per_row/K144r_fixed_W384_s45_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 400/400 | 215 (53.75%) | 375 (93.75%) | 99.55 | 102.88 |
