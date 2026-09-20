# Width-series analysis: `backend/reports/scale_grid_keff/K48`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 11.70 ± 3.97 | 40.65 ± 0.32 | 0.00 ± 0.00 | 208 |
| W192 | 192 | 8,150,208 | 53.68 ± 3.81 | 60.72 ± 3.10 | 30.67 ± 5.74 | 214 |
| W256 | 256 | 12,374,272 | 65.88 ± 1.25 | 81.10 ± 3.90 | 68.12 ± 5.00 | 216 |
| W384 | 384 | 23,378,304 | 70.50 ± 0.59 | 91.73 ± 0.12 | 85.48 ± 1.19 | 217 |
| W512 | 512 | 37,593,600 | 70.42 ± 3.27 | 90.75 ± 3.47 | 83.28 ± 6.89 | 211 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +41.98 | +13.90 | 0.00e+00 | yes | adopted |
| W128->W192 | coarse | +20.07 | +13.90 | 0.00e+00 | yes | adopted |
| W128->W192 | exact | +30.67 | +13.90 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | +12.20 | +13.90 | 0.00e+00 | yes | adopted |
| W192->W256 | coarse | +20.38 | +13.90 | 0.00e+00 | yes | adopted |
| W192->W256 | exact | +37.45 | +13.90 | 0.00e+00 | yes | adopted |
| W256->W384 | strict | +4.62 | +9.94 | 0.00e+00 | yes | adopted |
| W256->W384 | coarse | +10.63 | +12.75 | 0.00e+00 | yes | adopted |
| W256->W384 | exact | +17.37 | +13.90 | 0.00e+00 | yes | adopted |
| W384->W512 | strict | -0.08 | +1.29 | 4.24e-01 | NO | - |
| W384->W512 | coarse | -0.98 | -1.47 | 4.24e-01 | NO | - |
| W384->W512 | exact | -2.20 | +0.09 | 9.26e-01 | NO | - |
