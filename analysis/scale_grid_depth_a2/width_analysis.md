# Width-series analysis: `backend/reports/scale_grid_depth_a2`

| Scale | L | Params | Strict % | Coarse % | Exact tuple % | Latency ms |
|---|--:|--:|--:|--:|--:|--:|
| D2 | 2 | 12,756,864 | 66.86 ± 6.13 | 77.54 ± 7.91 | 72.27 ± 9.89 | 68 |
| D4 | 4 | 16,297,344 | 74.92 ± 2.05 | 87.60 ± 3.76 | 84.90 ± 5.38 | 116 |
| D6 | 6 | 19,837,824 | 73.62 ± 2.32 | 86.67 ± 2.75 | 83.13 ± 4.06 | 165 |
| D8 | 8 | 23,378,304 | 76.78 ± 0.92 | 90.10 ± 1.14 | 86.50 ± 2.52 | 209 |

## Adjacent-width contrasts (row-level McNemar, Stouffer, Holm over all)

| Step | Metric | Mean Δ pp | z | Holm p | Seeds same sign | Adopted |
|---|---|--:|--:|--:|---|---|
| D2->D4 | strict | +8.06 | +14.18 | 0.00e+00 | yes | adopted |
| D2->D4 | coarse | +10.06 | +14.18 | 0.00e+00 | yes | adopted |
| D2->D4 | exact | +12.63 | +14.81 | 0.00e+00 | yes | adopted |
| D4->D6 | strict | -1.73 | -4.07 | 1.44e-04 | NO | - |
| D4->D6 | coarse | -0.95 | -2.03 | 8.39e-02 | NO | - |
| D4->D6 | exact | -2.08 | -2.03 | 8.39e-02 | NO | - |
| D6->D8 | strict | +3.17 | +7.44 | 6.24e-13 | NO | - |
| D6->D8 | coarse | +3.43 | +6.93 | 2.12e-11 | NO | - |
| D6->D8 | exact | +3.37 | +5.93 | 1.19e-08 | NO | - |
