# CompactLM Direct Checkpoint Evaluation

- Model: `K48r_matched_W384_s43_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/runs/K48r_matched_W384_s43/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `417`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K48r_matched_W384_s43_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 417/417 | 166 (39.81%) | 397 (95.20%) | 218.0 | 240.77 |
