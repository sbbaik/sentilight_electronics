# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 66.80±2.19 | [65.60, 67.98] | 76.93±6.32 | [75.85, 77.98] | 204.29 |
| W192 | 100 | 3 | none | 8150208 | 68.58±2.09 | [67.40, 69.75] | 82.43±2.75 | [81.45, 83.38] | 210.08 |
| W256 | 100 | 3 | none | 12374272 | 68.45±4.51 | [67.26, 69.61] | 84.00±5.82 | [83.05, 84.91] | 214.74 |
| W384 | 100 | 3 | none | 23378304 | 69.13±5.36 | [67.95, 70.29] | 83.35±6.98 | [82.39, 84.27] | 221.81 |
| W512 | 100 | 3 | none | 37593600 | 71.77±3.38 | [70.61, 72.89] | 90.12±3.89 | [89.34, 90.85] | 212.43 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
