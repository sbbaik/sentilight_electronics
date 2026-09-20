# CompactLM Scale/Data Grid Summary

- Runs loaded: `18`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| D12 | 100 | 3 | none | 30459264 | 48.35±1.29 | [47.09, 49.62] | 84.77±2.16 | [83.84, 85.65] | 314.07 |
| D16 | 100 | 3 | none | 37540224 | 46.93±3.72 | [45.67, 48.20] | 81.03±7.76 | [80.02, 82.01] | 419.53 |
| D2 | 100 | 3 | none | 12756864 | 46.67±1.46 | [45.41, 47.93] | 83.78±1.78 | [82.83, 84.69] | 67.15 |
| D4 | 100 | 3 | none | 16297344 | 49.47±0.68 | [48.20, 50.73] | 87.65±0.83 | [86.79, 88.46] | 117.01 |
| D6 | 100 | 3 | none | 19837824 | 48.55±1.46 | [47.29, 49.82] | 84.68±3.76 | [83.75, 85.57] | 163.09 |
| D8 | 100 | 3 | none | 23378304 | 49.33±0.24 | [48.07, 50.60] | 84.93±0.68 | [84.01, 85.82] | 216.21 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
