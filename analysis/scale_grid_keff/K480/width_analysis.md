# Width-series analysis: `backend/reports/scale_grid_keff/K480`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 52.33 ± 6.15 | 71.35 ± 8.15 | 47.48 ± 9.75 | 208 |
| W192 | 192 | 8,150,208 | 57.02 ± 3.70 | 81.65 ± 4.44 | 71.00 ± 6.32 | 209 |
| W256 | 256 | 12,374,272 | 58.85 ± 2.01 | 83.83 ± 3.62 | 76.52 ± 4.19 | 212 |
| W384 | 384 | 23,378,304 | 59.93 ± 2.30 | 86.89 ± 2.98 | 81.34 ± 4.25 | 230 |
| W512 | 512 | 37,593,600 | 59.55 ± 2.01 | 85.61 ± 2.96 | 78.82 ± 4.03 | 226 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| W128->W192 | strict | +4.68 | +5.83 | 4.90e-08 | NO | - |
| W128->W192 | coarse | +10.30 | +9.07 | 0.00e+00 | NO | - |
| W128->W192 | exact | +23.52 | +13.35 | 0.00e+00 | yes | adopted |
| W192->W256 | strict | +1.83 | +3.85 | 7.60e-04 | yes | adopted |
| W192->W256 | coarse | +2.18 | +3.87 | 7.60e-04 | yes | adopted |
| W192->W256 | exact | +5.52 | +8.46 | 0.00e+00 | yes | adopted |
| W256->W384 | strict | +0.22 | +0.62 | 5.35e-01 | NO | - |
| W256->W384 | coarse | +1.43 | +2.78 | 2.15e-02 | NO | - |
| W256->W384 | exact | +2.27 | +3.74 | 9.30e-04 | NO | - |
| W384->W512 | strict | -0.38 | -1.28 | 4.02e-01 | NO | - |
| W384->W512 | coarse | -1.28 | -2.52 | 3.56e-02 | NO | - |
| W384->W512 | exact | -2.52 | -4.20 | 2.12e-04 | NO | - |
