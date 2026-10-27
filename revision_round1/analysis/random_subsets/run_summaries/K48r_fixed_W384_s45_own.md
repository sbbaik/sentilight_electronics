# CompactLM Direct Checkpoint Evaluation

- Model: `K48r_fixed_W384_s45_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/runs/K48r_fixed_W384_s45/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/K48r/test_rule.jsonl`
- Segment: `rule`
- Rows: `369`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/per_row/K48r_fixed_W384_s45_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 369/369 | 195 (52.85%) | 345 (93.50%) | 187.31 | 218.65 |
