# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 11.70±4.86 | [10.91, 12.54] | 40.65±0.39 | [39.41, 41.90] | 207.75 |
| W192 | 100 | 3 | none | 8150208 | 53.68±4.66 | [52.42, 54.94] | 60.72±3.79 | [59.47, 61.95] | 214.20 |
| W256 | 100 | 3 | none | 12374272 | 65.88±1.53 | [64.67, 67.07] | 81.10±4.77 | [80.09, 82.07] | 216.04 |
| W384 | 100 | 3 | none | 23378304 | 70.50±0.72 | [69.33, 71.64] | 91.73±0.15 | [91.01, 92.40] | 217.29 |
| W512 | 100 | 3 | none | 37593600 | 70.42±4.01 | [69.25, 71.56] | 90.75±4.25 | [89.99, 91.46] | 211.21 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
