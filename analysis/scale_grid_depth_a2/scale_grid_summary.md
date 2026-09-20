# CompactLM Scale/Data Grid Summary

- Runs loaded: `12`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| D2 | 100 | 3 | none | 12756864 | 71.13±2.52 | [69.97, 72.27] | 82.75±4.30 | [81.77, 83.68] | 68.39 |
| D4 | 100 | 3 | none | 16297344 | 75.35±2.65 | [74.24, 76.42] | 87.62±5.14 | [86.76, 88.43] | 115.54 |
| D6 | 100 | 3 | none | 19837824 | 73.62±2.32 | [72.49, 74.72] | 86.67±2.75 | [85.78, 87.50] | 164.55 |
| D8 | 100 | 3 | none | 23378304 | 76.78±0.92 | [75.70, 77.83] | 90.10±1.14 | [89.32, 90.83] | 209.23 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
