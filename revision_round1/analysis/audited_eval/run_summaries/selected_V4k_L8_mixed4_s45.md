# CompactLM Direct Checkpoint Evaluation

- Model: `selected_V4k_L8_mixed4_s45`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/doi_release/selected_d384_L8_V4k/mixed4_6_8bit_seed45.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/audited_requests/audited_requests_K240.jsonl`
- Segment: `rule`
- Rows: `240`
- Parameters: `15698304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/audited_eval/per_row/selected_V4k_L8_mixed4_s45.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 240/240 | 66 (27.50%) | 87 (36.25%) | 249.85 | 383.83 |
