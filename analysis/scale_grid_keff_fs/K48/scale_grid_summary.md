# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 62.15±2.83 | [60.92, 63.37] | 80.27±2.79 | [79.24, 81.25] | 205.24 |
| W192 | 100 | 3 | none | 8150208 | 70.85±1.18 | [69.69, 71.99] | 90.93±0.41 | [90.18, 91.63] | 209.07 |
| W256 | 100 | 3 | none | 12374272 | 70.55±3.48 | [69.38, 71.69] | 91.68±2.35 | [90.96, 92.36] | 210.23 |
| W384 | 100 | 3 | none | 23378304 | 72.13±3.18 | [70.99, 73.25] | 93.57±2.80 | [92.92, 94.16] | 214.86 |
| W512 | 100 | 3 | none | 37593600 | 72.17±2.97 | [71.02, 73.29] | 92.03±2.29 | [91.32, 92.69] | 205.00 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
