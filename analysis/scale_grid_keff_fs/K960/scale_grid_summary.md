# CompactLM Scale/Data Grid Summary

- Runs loaded: `15`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| W128 | 100 | 3 | none | 4679808 | 60.75±3.46 | [59.51, 61.98] | 50.38±4.32 | [49.12, 51.65] | 196.65 |
| W192 | 100 | 3 | none | 8150208 | 64.80±3.53 | [63.58, 66.00] | 62.87±3.62 | [61.64, 64.08] | 207.36 |
| W256 | 100 | 3 | none | 12374272 | 67.82±2.88 | [66.62, 68.99] | 76.20±8.50 | [75.11, 77.26] | 203.18 |
| W384 | 100 | 3 | none | 23378304 | 69.18±5.62 | [68.00, 70.34] | 80.20±8.97 | [79.17, 81.19] | 211.99 |
| W512 | 100 | 3 | none | 37593600 | 71.95±0.58 | [70.80, 73.07] | 85.45±1.07 | [84.54, 86.32] | 207.65 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
