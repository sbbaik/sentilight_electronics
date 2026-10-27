# CompactLM Direct Checkpoint Evaluation

- Model: `selected_V4k_L8_s42`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/doi_release/selected_d384_L8_V4k/fp32_seed42.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/audited_requests/audited_requests_K240.jsonl`
- Segment: `rule`
- Rows: `240`
- Parameters: `15698304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/audited_eval/per_row/selected_V4k_L8_s42.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 240/240 | 68 (28.33%) | 95 (39.58%) | 3203.3 | 4098.06 |
