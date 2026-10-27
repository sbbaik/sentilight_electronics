# CompactLM Direct Checkpoint Evaluation

- Model: `K48r_fixed_W384_s46_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/runs/K48r_fixed_W384_s46/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/K48r/test_rule.jsonl`
- Segment: `rule`
- Rows: `417`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K48r_fixed_W384_s46_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 417/417 | 167 (40.05%) | 400 (95.92%) | 120.66 | 128.58 |
