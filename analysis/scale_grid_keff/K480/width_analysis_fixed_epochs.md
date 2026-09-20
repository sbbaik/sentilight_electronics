# Width-series analysis: `backend/reports/scale_grid_keff/K480`

| Scale | d | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| W128 | 128 | 4,679,808 | 52.33 ± 5.02 | 71.35 ± 6.65 | 47.48 ± 7.96 | 208 |
| W192 | 192 | 8,150,208 | 57.02 ± 3.02 | 81.65 ± 3.63 | 71.00 ± 5.16 | 209 |
| W256 | 256 | 12,374,272 | 58.85 ± 1.64 | 83.83 ± 2.95 | 76.52 ± 3.42 | 212 |
| W384 | 384 | 23,378,304 | 59.07 ± 0.96 | 85.27 ± 1.07 | 78.78 ± 2.02 | 215 |
| W512 | 512 | 37,593,600 | 60.60 ± 0.43 | 87.57 ± 0.96 | 80.93 ± 1.91 | 212 |

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
| W256->W384 | coarse | +1.43 | +2.78 | 1.08e-02 | NO | - |
| W256->W384 | exact | +2.27 | +3.74 | 7.60e-04 | NO | - |
| W384->W512 | strict | +1.53 | +3.68 | 7.60e-04 | NO | - |
| W384->W512 | coarse | +2.30 | +4.54 | 4.59e-05 | yes | adopted |
| W384->W512 | exact | +2.15 | +3.84 | 7.60e-04 | NO | - |
