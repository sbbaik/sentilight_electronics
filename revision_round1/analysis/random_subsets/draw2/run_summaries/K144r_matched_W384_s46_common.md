# CompactLM Direct Checkpoint Evaluation

- Model: `K144r_matched_W384_s46_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/runs/K144r_matched_W384_s46/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `417`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K144r_matched_W384_s46_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 417/417 | 158 (37.89%) | 371 (88.97%) | 121.35 | 130.65 |
