**T10_final_models.** Candidate configurations at five seeds and their mixed 4/6/8-bit quantized versions. Latency = KV-cache-free 96-step reference decoder (GPU); quantized rows were evaluated with the load-time-dequantizing KV-cache runtime, so their latency is not a quantization speed-up. Values are mean ± sample SD (n − 1) across seeds; n is given in the seeds column.

| configuration | seeds | parameters | fp32 weights MB | exact tuple % | coarse % | strict % | invalid JSON % | latency mean / p95 ms |
|---|---|---|---|---|---|---|---|---|
| W384 (deployed cfg: d384 L8 V24k-prod) | 5 | 23,378,304 | 93.5 | 80.8 ± 3.6 | 85.8 ± 2.7 | 49.3 ± 1.4 | 0.00 | 216 / 234 |
| D4 (d384 L4 V24k-prod) | 5 | 16,297,344 | 65.2 | 81.7 ± 4.9 | 86.1 ± 3.3 | 48.8 ± 1.2 | 0.00 | 118 / 127 |
| V2 V4k (d384 L8 V4k-natural) | 5 | 15,698,304 | 62.8 | 86.5 ± 1.8 | 90.4 ± 1.1 | 51.4 ± 0.6 | 0.00 | 203 / 225 |
| C4kL4 (d384 L4 V4k-natural) | 5 | 8,617,344 | 34.5 | 82.0 ± 6.4 | 86.8 ± 4.8 | 49.2 ± 2.3 | 0.01 | 107 / 114 |
| V2 V4k mixed-4/6/8-bit (KV-cache eval runtime) | 5 | 15,698,304 | 62.8 | 86.3 ± 1.9 | 90.3 ± 1.3 | 51.3 ± 0.8 | 0.00 | 108 / 121 |
| C4kL4 mixed-4/6/8-bit (KV-cache eval runtime) | 5 | 8,617,344 | 34.5 | 81.5 ± 6.1 | 86.5 ± 4.7 | 49.1 ± 2.2 | 0.01 | 58 / 63 |
| quantization equivalence (exact, q − fp32): selected model | 5 |  | 17.1 MB mixed-bit file | -0.19 pp, 90 % CI [-0.52, +0.14] | TOST ±3 pp: pass |  |  |  |
| quantization equivalence (exact, q − fp32): d384 L4 V4k | 5 |  | 12.3 MB mixed-bit file | -0.42 pp, 90 % CI [-1.20, +0.36] | TOST ±3 pp: pass |  |  |  |

Source: `backend/reports/scale_grid_combo/final_model_table.json; scale_grid_vocab_natural_q4/quant_equivalence.json; scale_grid_combo_q4/quant_equivalence.json`
