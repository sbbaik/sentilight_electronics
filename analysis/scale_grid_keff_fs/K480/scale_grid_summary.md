# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 48.15±4.40 | [46.89, 49.42] | 56.13±3.41 | [54.87, 57.38] | 202.73 |
| W192 | 100 | 3 | none | 8150208 | 55.90±0.64 | [54.64, 57.15] | 76.23±1.45 | [75.14, 77.29] | 203.21 |
| W256 | 100 | 3 | none | 12374272 | 56.15±2.25 | [54.89, 57.40] | 79.43±3.93 | [78.39, 80.44] | 204.68 |
| W384 | 100 | 3 | none | 23378304 | 59.73±1.37 | [58.49, 60.97] | 85.15±3.01 | [84.23, 86.03] | 216.62 |
| W512 | 100 | 3 | none | 37593600 | 61.50±0.18 | [60.26, 62.72] | 87.58±0.13 | [86.72, 88.39] | 204.00 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
