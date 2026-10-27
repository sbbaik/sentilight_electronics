# CompactLM Direct Checkpoint Evaluation

- Model: `K96r_fixed_W384_s42_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/runs/K96r_fixed_W384_s42/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/K96r/test_rule.jsonl`
- Segment: `rule`
- Rows: `769`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/per_row/K96r_fixed_W384_s42_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 769/769 | 385 (50.07%) | 726 (94.41%) | 91.76 | 93.79 |
