# CompactLM Direct Checkpoint Evaluation

- Model: `K96r_matched_W256_s44_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/runs/K96r_matched_W256_s44/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/K96r/test_rule.jsonl`
- Segment: `rule`
- Rows: `769`
- Parameters: `12374272`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/per_row/K96r_matched_W256_s44_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 769/769 | 372 (48.37%) | 684 (88.95%) | 70.52 | 81.28 |
