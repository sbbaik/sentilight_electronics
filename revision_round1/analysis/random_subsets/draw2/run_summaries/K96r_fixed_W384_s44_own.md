# CompactLM Direct Checkpoint Evaluation

- Model: `K96r_fixed_W384_s44_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/runs/K96r_fixed_W384_s44/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/K96r/test_rule.jsonl`
- Segment: `rule`
- Rows: `796`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K96r_fixed_W384_s44_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 796/796 | 363 (45.60%) | 736 (92.46%) | 106.43 | 126.91 |
