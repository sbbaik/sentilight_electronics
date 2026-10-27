# CompactLM Direct Checkpoint Evaluation

- Model: `decoder_lead_s43`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/doi_release/selected_d384_L8_V4k/fp32_seed43.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/datasets/dev_lead.jsonl`
- Segment: `rule`
- Rows: `2000`
- Parameters: `15698304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/head_ablation/per_row/decoder_lead_s43.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 2000/2000 | 863 (43.15%) | 1543 (77.15%) | 326.49 | 784.2 |
