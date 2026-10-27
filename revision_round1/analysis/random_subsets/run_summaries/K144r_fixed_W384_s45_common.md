# CompactLM Direct Checkpoint Evaluation

- Model: `K144r_fixed_W384_s45_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/runs/K144r_fixed_W384_s45/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `369`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/per_row/K144r_fixed_W384_s45_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 369/369 | 197 (53.39%) | 339 (91.87%) | 195.23 | 230.07 |
