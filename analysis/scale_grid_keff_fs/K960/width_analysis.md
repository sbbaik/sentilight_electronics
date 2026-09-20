# Width-series analysis: `backend/reports/scale_grid_keff_fs/K960`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 60.75 ± 3.46 | 50.38 ± 4.32 | 0.22 ± 0.08 | 197 |
| W192 | 192 | 8,150,208 | 64.80 ± 3.53 | 62.87 ± 3.62 | 19.08 ± 1.49 | 207 |
| W256 | 256 | 12,374,272 | 68.36 ± 2.72 | 76.58 ± 6.68 | 56.02 ± 13.35 | 208 |
| W384 | 384 | 23,378,304 | 69.55 ± 4.81 | 81.48 ± 8.05 | 69.39 ± 13.16 | 215 |
| W512 | 512 | 37,593,600 | 71.95 ± 0.58 | 85.45 ± 1.07 | 76.12 ± 2.15 | 208 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +4.05 | +6.17 | 3.98e-09 | NO | - |
| W128->W192 | coarse | +12.48 | +11.24 | 0.00e+00 | yes | adopted |
| W128->W192 | exact | +18.87 | +13.90 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | +3.02 | +5.71 | 5.77e-08 | NO | - |
| W192->W256 | coarse | +13.33 | +10.97 | 0.00e+00 | yes | adopted |
| W192->W256 | exact | +36.40 | +13.90 | 0.00e+00 | yes | adopted |
| W256->W384 | strict | +1.19 | +3.56 | 3.66e-04 | NO | - |
| W256->W384 | coarse | +4.90 | +7.92 | 1.55e-14 | NO | - |
| W256->W384 | exact | +13.37 | +10.66 | 0.00e+00 | NO | - |
| W384->W512 | strict | +2.77 | +4.26 | 4.10e-05 | NO | - |
| W384->W512 | coarse | +5.25 | +5.39 | 2.82e-07 | NO | - |
| W384->W512 | exact | +8.40 | +5.24 | 4.80e-07 | NO | - |
