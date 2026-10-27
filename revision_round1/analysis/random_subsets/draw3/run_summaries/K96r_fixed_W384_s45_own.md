# CompactLM Direct Checkpoint Evaluation

- Model: `K96r_fixed_W384_s45_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/runs/K96r_fixed_W384_s45/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw3/K96r/test_rule.jsonl`
- Segment: `rule`
- Rows: `793`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/per_row/K96r_fixed_W384_s45_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 793/793 | 412 (51.95%) | 706 (89.03%) | 121.11 | 129.19 |
