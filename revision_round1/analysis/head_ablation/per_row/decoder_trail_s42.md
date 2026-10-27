# CompactLM Direct Checkpoint Evaluation

- Model: `decoder_trail_s42`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/doi_release/selected_d384_L8_V4k/fp32_seed42.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/datasets/dev_trail.jsonl`
- Segment: `rule`
- Rows: `2000`
- Parameters: `15698304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/per_row/decoder_trail_s42.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 2000/2000 | 146 (7.30%) | 358 (17.90%) | 318.5 | 594.05 |
