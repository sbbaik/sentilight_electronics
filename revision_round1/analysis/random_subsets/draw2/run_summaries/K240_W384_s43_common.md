# CompactLM Direct Checkpoint Evaluation

- Model: `K240_W384_s43_common`
- Checkpoint: `/home/sbbaik/Sentilight_Paper_2/Implement_New_Android_v6/backend/models/compact_llm/scale_grid_runs_width/W384/seed_43/f100/sft/compactlm_from_scratch_best.pt`
- Dataset: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/data/datasets/random_subsets/draw2/common_test_K48r.jsonl`
- Segment: `rule`
- Rows: `417`
- Parameters: `23378304`
- Per-row JSONL: `/home/sbbaik/Sentilight_Paper_2/MDPI_Electronics_review_1st_round/analysis/random_subsets/draw2/per_row/K240_W384_s43_common.jsonl`

| Success | Strict | Coarse | Mean Latency | P95 Latency |
|---:|---:|---:|---:|---:|
| 417/417 | 159 (38.13%) | 362 (86.81%) | 162.71 | 253.47 |
