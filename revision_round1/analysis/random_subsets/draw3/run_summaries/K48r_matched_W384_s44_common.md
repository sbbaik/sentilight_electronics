# CompactLM Direct Checkpoint Evaluation

- Model: `K48r_matched_W384_s44_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/runs/K48r_matched_W384_s44/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw3/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `400`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw3/per_row/K48r_matched_W384_s44_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 400/400 | 200 (50.00%) | 358 (89.50%) | 186.79 | 258.11 |
