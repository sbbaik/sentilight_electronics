# Width-series analysis: `backend/reports/scale_grid_width_v4k`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| X224 | 224 | 5,774,048 | 49.45 ± 1.44 | 86.56 ± 1.73 | 79.03 ± 3.11 | 202 |
| X256 | 256 | 7,254,272 | 48.08 ± 1.13 | 82.60 ± 4.02 | 75.97 ± 4.91 | 201 |
| X320 | 320 | 11,197,760 | 51.00 ± 1.53 | 88.89 ± 2.86 | 83.77 ± 3.39 | 197 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| X224->X256 | strict | -1.37 | -4.42 | 9.68e-06 | yes | adopted |
| X224->X256 | coarse | -3.96 | -9.10 | 0.00e+00 | NO | - |
| X224->X256 | exact | -3.06 | -5.46 | 9.46e-08 | NO | - |
| X256->X320 | strict | +2.92 | +8.96 | 0.00e+00 | NO | - |
| X256->X320 | coarse | +6.29 | +10.25 | 0.00e+00 | NO | - |
| X256->X320 | exact | +7.80 | +11.15 | 0.00e+00 | NO | - |
