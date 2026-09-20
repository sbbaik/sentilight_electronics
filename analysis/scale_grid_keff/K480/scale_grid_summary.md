# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 52.33±6.15 | [51.07, 53.60] | 71.35±8.15 | [70.19, 72.48] | 207.80 |
| W192 | 100 | 3 | none | 8150208 | 57.02±3.70 | [55.76, 58.26] | 81.65±4.44 | [80.65, 82.61] | 208.52 |
| W256 | 100 | 3 | none | 12374272 | 58.85±2.01 | [57.60, 60.09] | 83.83±3.62 | [82.88, 84.74] | 212.04 |
| W384 | 100 | 3 | none | 23378304 | 59.07±1.18 | [57.82, 60.30] | 85.27±1.31 | [84.35, 86.14] | 214.68 |
| W512 | 100 | 3 | none | 37593600 | 60.60±0.53 | [59.36, 61.83] | 87.57±1.18 | [86.71, 88.38] | 211.91 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
