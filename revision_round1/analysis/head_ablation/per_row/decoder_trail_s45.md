# CompactLM Direct Checkpoint Evaluation

- Model: `decoder_trail_s45`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/doi_release/selected_d384_L8_V4k/fp32_seed45.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/datasets/dev_trail.jsonl`
- Segment: `rule`
- Rows: `2000`
- Parameters: `15698304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/per_row/decoder_trail_s45.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 2000/2000 | 201 (10.05%) | 348 (17.40%) | 314.13 | 630.94 |
