# CompactLM Scale/Data Grid Summary

- Runs loaded: `3`
- Expected seeds: `42, 43, 44`

| Scale | Data % | Runs | Missing Seeds | Params | Strict mean±std | Strict pooled 95% CI | Coarse mean±std | Coarse pooled 95% CI | Mean latency ms |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| V8k | 100 | 3 | none | 17234304 | 49.27±1.29 | [48.00, 50.53] | 86.98±2.63 | [86.11, 87.81] | 198.66 |

Pre-registered interpretation rule:

- Support prediction 1 if 8M->23M and 23M->60M improvements are both below 3.5%p.
- Reject or reduce prediction 1 if 23M->60M improves by at least 3.5%p with statistical support.
- Move the estimated plateau downward if only 3M->8M improves substantially.
