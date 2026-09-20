# Width-series analysis: `backend/reports/scale_grid_keff_fs/K480`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 48.15 ± 4.40 | 56.13 ± 3.41 | 6.55 ± 1.13 | 203 |
| W192 | 192 | 8,150,208 | 54.18 ± 2.50 | 73.98 ± 3.29 | 54.64 ± 6.48 | 205 |
| W256 | 256 | 12,374,272 | 56.89 ± 2.04 | 80.47 ± 3.39 | 69.62 ± 2.88 | 209 |
| W384 | 384 | 23,378,304 | 59.73 ± 1.37 | 85.15 ± 3.01 | 78.20 ± 4.13 | 217 |
| W512 | 512 | 37,593,600 | 61.50 ± 0.18 | 87.58 ± 0.13 | 79.90 ± 0.98 | 204 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +7.75 | +11.39 | 0.00e+00 | yes | adopted |
| W128->W192 | coarse | +20.10 | +13.90 | 0.00e+00 | yes | adopted |
| W128->W192 | exact | +51.67 | +13.90 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | +2.71 | +6.84 | 3.23e-11 | NO | - |
| W192->W256 | coarse | +6.49 | +11.33 | 0.00e+00 | NO | - |
| W192->W256 | exact | +14.98 | +16.31 | 0.00e+00 | yes | adopted |
| W256->W384 | strict | +3.58 | +6.92 | 2.62e-11 | yes | adopted |
| W256->W384 | coarse | +5.72 | +6.89 | 2.84e-11 | yes | adopted |
| W256->W384 | exact | +9.73 | +10.79 | 0.00e+00 | yes | adopted |
| W384->W512 | strict | +1.77 | +4.67 | 6.39e-06 | yes | adopted |
| W384->W512 | coarse | +2.43 | +4.74 | 6.39e-06 | NO | - |
| W384->W512 | exact | +1.70 | +2.89 | 3.84e-03 | NO | - |
