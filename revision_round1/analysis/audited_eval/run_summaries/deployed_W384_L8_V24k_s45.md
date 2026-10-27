# CompactLM Direct Checkpoint Evaluation

- Model: `deployed_W384_L8_V24k_s45`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/models/reference_W384/fp32_seed45.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/audited_requests/audited_requests_K240.jsonl`
- Segment: `rule`
- Rows: `240`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/audited_eval/per_row/deployed_W384_L8_V24k_s45.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 240/240 | 64 (26.67%) | 92 (38.33%) | 3377.29 | 4057.86 |
