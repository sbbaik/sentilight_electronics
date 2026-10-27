# CompactLM Direct Checkpoint Evaluation

- Model: `K144r_matched_W384_s42_own`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/runs/K144r_matched_W384_s42/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/K144r/test_rule.jsonl`
- Segment: `rule`
- Rows: `1175`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K144r_matched_W384_s42_own.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 1175/1175 | 531 (45.19%) | 1030 (87.66%) | 118.32 | 129.05 |
