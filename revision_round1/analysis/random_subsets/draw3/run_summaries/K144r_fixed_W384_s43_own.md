# CompactLM Direct Checkpoint Evaluation

- Model: `K144r_fixed_W384_s43_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/runs/K144r_fixed_W384_s43/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw3/K144r/test_rule.jsonl`
- Segment: `rule`
- Rows: `1196`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/per_row/K144r_fixed_W384_s43_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 1196/1196 | 561 (46.91%) | 1057 (88.38%) | 120.44 | 129.26 |
