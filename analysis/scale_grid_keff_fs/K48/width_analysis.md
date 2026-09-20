# Width-series analysis: `backend/reports/scale_grid_keff_fs/K48`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 62.99 ± 5.14 | 81.44 ± 4.98 | 67.55 ± 5.22 | 206 |
| W192 | 192 | 8,150,208 | 70.00 ± 2.40 | 90.37 ± 3.03 | 80.98 ± 3.70 | 209 |
| W256 | 256 | 12,374,272 | 70.55 ± 3.48 | 91.68 ± 2.35 | 82.92 ± 5.38 | 210 |
| W384 | 384 | 23,378,304 | 72.13 ± 3.18 | 93.57 ± 2.80 | 89.02 ± 2.07 | 215 |
| W512 | 512 | 37,593,600 | 72.17 ± 2.97 | 92.03 ± 2.29 | 86.02 ± 3.71 | 205 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +7.01 | +14.78 | 0.00e+00 | yes | adopted |
| W128->W192 | coarse | +8.93 | +16.69 | 0.00e+00 | yes | adopted |
| W128->W192 | exact | +13.43 | +17.95 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | -0.30 | +0.21 | 1.00e+00 | NO | - |
| W192->W256 | coarse | +0.75 | +2.46 | 5.63e-02 | NO | - |
| W192->W256 | exact | +0.93 | +1.57 | 3.52e-01 | NO | - |
| W256->W384 | strict | +1.58 | +2.60 | 4.66e-02 | NO | - |
| W256->W384 | coarse | +1.88 | +5.20 | 1.42e-06 | NO | - |
| W256->W384 | exact | +6.10 | +8.24 | 2.00e-15 | NO | - |
| W384->W512 | strict | +0.03 | -0.56 | 1.00e+00 | NO | - |
| W384->W512 | coarse | -1.53 | -4.74 | 1.26e-05 | NO | - |
| W384->W512 | exact | -3.00 | -5.71 | 9.28e-08 | NO | - |
