**T09_seed_level_contrasts.** Seed-level statistics for the main paired contrasts (exact tuple match, five seeds): mean and SD of per-seed differences, 90 % t confidence interval (df = 4), hierarchical bootstrap 95 % interval (seeds, then rows), and the number of seeds with a positive difference. The prospectively specified all-seeds direction rule is met only when the last column reads 5/5.

| contrast | mean Δ pp | SD | 90 % CI (seed t) | 95 % CI (hierarchical bootstrap) / sensitivity | seeds > 0 |
|---|---|---|---|---|---|
| deployed cfg → selected (d384 L8: V24k → V4k) | +5.79 | 4.90 | [+1.1, +10.5] | [+1.4, +9.1] | 4/5 |
| deployed cfg → d384 L4 V24k | +0.92 | 8.25 | [-7.0, +8.8] | [-6.6, +5.8] | 4/5 |
| deployed cfg → d384 L4 V4k | +1.22 | 8.21 | [-6.6, +9.1] | [-5.3, +7.6] | 3/5 |
| selected → d384 L4 V4k | -4.57 | 5.83 | [-10.1, +1.0] | [-9.2, +0.0] | 2/5 |
| d256 → d384 (both V4k) | +10.57 | 4.65 | [+6.1, +15.0] | [+6.8, +14.2] | 5/5 |
| d320 → d384 (both V4k) | +2.77 | 4.25 | [-1.3, +6.8] | [-1.0, +5.7] | 4/5 |
| d224 → d256 (both V4k) | -3.06 | 5.27 | [-8.1, +2.0] | [-7.4, +1.1] | 1/5 |
| tokenizer-configuration × width interaction (V4k384−X256) − (W384−W256) | +7.84 |  | paired [−1.9, +17.5]; unpaired Welch [+1.9, +13.8] | permutation p = 0.106 | 4/5 |

Source: `backend/reports/scale_grid_combo/seed_level_stats.json; scale_grid_width_v4k/seed_level_stats.json; interaction_sensitivity.json`
