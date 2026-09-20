# CompactLM Scale/Data Grid Summary

- Runs loaded: `21`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 43.22±2.04 | [41.97, 44.47] | 73.20±1.51 | [72.06, 74.31] | 209.08 |
| W192 | 100 | 3 | none | 8150208 | 46.90±2.52 | [45.64, 48.16] | 82.30±2.43 | [81.31, 83.24] | 213.90 |
| W224 | 100 | 3 | none | 10254048 | 44.40±2.73 | [43.15, 45.66] | 77.23±6.88 | [76.16, 78.28] | 214.71 |
| W256 | 100 | 3 | none | 12374272 | 48.15±1.39 | [46.89, 49.42] | 85.48±2.50 | [84.57, 86.35] | 212.97 |
| W320 | 100 | 3 | none | 17597760 | 48.82±0.87 | [47.55, 50.08] | 87.20±1.21 | [86.33, 88.02] | 215.44 |
| W384 | 100 | 3 | none | 23378304 | 49.33±0.24 | [48.07, 50.60] | 84.93±0.68 | [84.01, 85.82] | 218.71 |
| W512 | 100 | 3 | none | 37593600 | 50.88±2.82 | [49.62, 52.15] | 88.62±4.36 | [87.79, 89.40] | 216.57 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
