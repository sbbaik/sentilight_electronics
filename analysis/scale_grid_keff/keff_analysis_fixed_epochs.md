# K_eff series analysis (tau = 0.1)

- K240 column: `/home/sbbaik/Sentilight_Paper_2/Implement_New_Android_v6/backend/reports/scale_grid_width` (W series); other columns: `backend/reports/scale_grid_keff/<P>`
- Widths common to every column: [128, 192, 256, 384, 512]

## exact (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 0.0 ± 0.0 | 30.7 ± 7.0 | · | 68.1 ± 6.1 | · | 85.5 ± 1.5 | 83.3 ± 8.4 | 384 | 256 | W384->W512 |
| 240 | 49.5 ± 4.8 | 70.6 ± 5.4 | 70.6 ± 6.8 | 78.0 ± 4.0 | 81.9 ± 1.9 | 80.8 ± 3.6 | 81.6 ± 5.3 | 384 | 192 | W192->W224 |
| 480 | 47.5 ± 9.8 | 71.0 ± 6.3 | · | 76.5 ± 4.2 | · | 81.3 ± 4.2 | 78.8 ± 4.0 | 384 | 192 | W256->W384 |
| 960 | 51.3 ± 9.2 | 68.2 ± 3.6 | · | 74.7 ± 9.5 | · | 79.9 ± 7.8 | 79.0 ± 9.7 | 384 | 192 | W256->W384 |

log d* vs log K_eff: slope = 0.000, R² = nan (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## coarse (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 40.6 ± 0.4 | 60.7 ± 3.8 | · | 81.1 ± 4.8 | · | 91.7 ± 0.2 | 90.8 ± 4.3 | 384 | 256 | W384->W512 |
| 240 | 69.6 ± 5.2 | 80.0 ± 4.1 | 78.5 ± 5.4 | 84.3 ± 2.8 | 87.2 ± 1.2 | 85.8 ± 2.7 | 86.9 ± 4.1 | 384 | 192 | W192->W224 |
| 480 | 71.3 ± 8.1 | 81.6 ± 4.4 | · | 83.8 ± 3.6 | · | 86.9 ± 3.0 | 85.6 ± 3.0 | 384 | 192 | W256->W384 |
| 960 | 76.9 ± 6.3 | 82.4 ± 2.7 | · | 84.0 ± 5.8 | · | 86.4 ± 6.6 | 86.2 ± 6.2 | 384 | 192 | - |

log d* vs log K_eff: slope = 0.000, R² = nan (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## strict (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 11.7 ± 4.9 | 53.7 ± 4.7 | · | 65.9 ± 1.5 | · | 70.5 ± 0.7 | 70.4 ± 4.0 | 256 | 192 | W384->W512 |
| 240 | 41.0 ± 3.5 | 45.7 ± 2.6 | 44.9 ± 2.1 | 47.4 ± 1.6 | 48.8 ± 0.9 | 49.3 ± 1.4 | 49.9 ± 2.5 | 384 | 192 | W256->W320 |
| 480 | 52.3 ± 6.2 | 57.0 ± 3.7 | · | 58.9 ± 2.0 | · | 59.9 ± 2.3 | 59.5 ± 2.0 | 384 | 192 | W256->W384 |
| 960 | 66.8 ± 2.2 | 68.6 ± 2.1 | · | 68.4 ± 4.5 | · | 70.7 ± 4.5 | 70.4 ± 3.1 | 384 | 384 | - |

log d* vs log K_eff: slope = 0.142, R² = 0.805 (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## Absolute-level knee (exact tuple match): smallest d reaching the level

| K_eff | >= 50% | >= 60% | >= 70% | >= 80% |
|--:|--:|--:|--:|--:|
| 48 | 256 | 256 | 384 | 384 |
| 240 | 192 | 192 | 192 | 384 |
| 480 | 192 | 192 | 192 | 384 |
| 960 | 128 | 192 | 256 | > 512 |

- level 50%: pairs [(48, 256), (240, 192), (480, 192), (960, 128)]; log d* vs log K_eff slope = -0.205 (R² = 0.850)
- level 60%: pairs [(48, 256), (240, 192), (480, 192), (960, 192)]; log d* vs log K_eff slope = -0.101 (R² = 0.805)
- level 70%: pairs [(48, 384), (240, 192), (480, 192), (960, 256)]; log d* vs log K_eff slope = -0.169 (R² = 0.434)
- level 80%: pairs [(48, 384), (240, 384), (480, 384)]; log d* vs log K_eff slope = 0.000 (R² = nan)

