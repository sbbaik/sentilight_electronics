# Width-series analysis: `backend/reports/scale_grid_keff/K960`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 66.80 ± 1.78 | 76.93 ± 5.16 | 51.27 ± 7.52 | 204 |
| W192 | 192 | 8,150,208 | 68.58 ± 1.71 | 82.43 ± 2.24 | 68.25 ± 2.98 | 210 |
| W256 | 256 | 12,374,272 | 68.45 ± 3.68 | 84.00 ± 4.75 | 74.67 ± 7.79 | 215 |
| W384 | 384 | 23,378,304 | 69.13 ± 4.38 | 83.35 ± 5.70 | 75.57 ± 5.91 | 222 |
| W512 | 512 | 37,593,600 | 71.77 ± 2.76 | 90.12 ± 3.17 | 85.20 ± 3.60 | 212 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +1.78 | +3.96 | 3.76e-04 | NO | - |
| W128->W192 | coarse | +5.50 | +5.00 | 3.93e-06 | NO | - |
| W128->W192 | exact | +16.98 | +12.17 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | -0.13 | +0.20 | 8.44e-01 | NO | - |
| W192->W256 | coarse | +1.57 | +2.96 | 9.15e-03 | NO | - |
| W192->W256 | exact | +6.42 | +7.78 | 6.39e-14 | yes | adopted |
| W256->W384 | strict | +0.68 | +3.37 | 3.04e-03 | NO | - |
| W256->W384 | coarse | -0.65 | +2.90 | 9.15e-03 | NO | - |
| W256->W384 | exact | +0.90 | +4.23 | 1.41e-04 | NO | - |
| W384->W512 | strict | +2.63 | +6.47 | 7.82e-10 | NO | - |
| W384->W512 | coarse | +6.77 | +11.30 | 0.00e+00 | yes | adopted |
| W384->W512 | exact | +9.63 | +13.66 | 0.00e+00 | yes | adopted |
