# K_eff series analysis (tau = 0.1)

- K240 column: `/home/sbbaik/Sentilight_Paper_2/Implement_New_Android_v6/backend/reports/scale_grid_width` (W series); other columns: `backend/reports/scale_grid_keff_fs/<P>`
- Widths common to every column: [128, 192, 256, 384, 512]

## exact (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 67.5 ± 5.2 | 81.0 ± 3.7 | · | 82.9 ± 5.4 | · | 89.0 ± 2.1 | 86.0 ± 3.7 | 384 | 192 | W192->W256 |
| 240 | 49.5 ± 4.8 | 70.6 ± 5.4 | 70.6 ± 6.8 | 78.0 ± 4.0 | 81.9 ± 1.9 | 80.8 ± 3.6 | 81.6 ± 5.3 | 384 | 192 | W192->W224 |
| 480 | 6.5 ± 1.1 | 54.6 ± 6.5 | · | 69.6 ± 2.9 | · | 78.2 ± 4.1 | 79.9 ± 1.0 | 384 | 192 | W384->W512 |
| 960 | 0.2 ± 0.1 | 19.1 ± 1.5 | · | 56.0 ± 13.3 | · | 69.4 ± 13.2 | 76.1 ± 2.2 | 384 | 256 | W256->W384 |

log d* vs log K_eff: slope = 0.000, R² = nan (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## coarse (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 81.4 ± 5.0 | 90.4 ± 3.0 | · | 91.7 ± 2.4 | · | 93.6 ± 2.8 | 92.0 ± 2.3 | 384 | 192 | W192->W256 |
| 240 | 69.6 ± 5.2 | 80.0 ± 4.1 | 78.5 ± 5.4 | 84.3 ± 2.8 | 87.2 ± 1.2 | 85.8 ± 2.7 | 86.9 ± 4.1 | 384 | 192 | W192->W224 |
| 480 | 56.1 ± 3.4 | 74.0 ± 3.3 | · | 80.5 ± 3.4 | · | 85.2 ± 3.0 | 87.6 ± 0.1 | 384 | 192 | W192->W256 |
| 960 | 50.4 ± 4.3 | 62.9 ± 3.6 | · | 76.6 ± 6.7 | · | 81.5 ± 8.0 | 85.5 ± 1.1 | 512 | 256 | W256->W384 |

log d* vs log K_eff: slope = 0.074, R² = 0.435 (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## strict (mean ± SD over seeds)

| K_eff | d=128 | d=192 | d=224 | d=256 | d=320 | d=384 | d=512 | d* | largest gain at | first non-adopted step |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 48 | 63.0 ± 5.1 | 70.0 ± 2.4 | · | 70.5 ± 3.5 | · | 72.1 ± 3.2 | 72.2 ± 3.0 | 384 | 192 | W192->W256 |
| 240 | 41.0 ± 3.5 | 45.7 ± 2.6 | 44.9 ± 2.1 | 47.4 ± 1.6 | 48.8 ± 0.9 | 49.3 ± 1.4 | 49.9 ± 2.5 | 384 | 192 | W256->W320 |
| 480 | 48.1 ± 4.4 | 54.2 ± 2.5 | · | 56.9 ± 2.0 | · | 59.7 ± 1.4 | 61.5 ± 0.2 | 512 | 192 | W192->W256 |
| 960 | 60.8 ± 3.5 | 64.8 ± 3.5 | · | 68.4 ± 2.7 | · | 69.5 ± 4.8 | 71.9 ± 0.6 | 512 | 192 | - |

log d* vs log K_eff: slope = 0.107, R² = 0.689 (slope 1.0 would mean d* ∝ K_eff; slope 0 means the knee does not move)

## Absolute-level knee (exact tuple match): smallest d reaching the level

| K_eff | >= 50% | >= 60% | >= 70% | >= 80% |
|--:|--:|--:|--:|--:|
| 48 | 128 | 128 | 192 | 192 |
| 240 | 192 | 192 | 192 | 384 |
| 480 | 192 | 256 | 384 | > 512 |
| 960 | 256 | 384 | 512 | > 512 |

- level 50%: pairs [(48, 128), (240, 192), (480, 192), (960, 256)]; log d* vs log K_eff slope = 0.216 (R² = 0.943)
- level 60%: pairs [(48, 128), (240, 192), (480, 256), (960, 384)]; log d* vs log K_eff slope = 0.353 (R² = 0.957)
- level 70%: pairs [(48, 192), (240, 192), (480, 384), (960, 512)]; log d* vs log K_eff slope = 0.333 (R² = 0.737)
- level 80%: pairs [(48, 192), (240, 384)]; log d* vs log K_eff slope = 0.431 (R² = 1.000)

