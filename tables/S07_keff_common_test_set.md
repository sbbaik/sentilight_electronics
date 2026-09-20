**S07_keff_common_test_set.** K-series models evaluated on one fixed test set — the K48 policy's 2,000-row test_rule, i.e. identical utterances for every model (supplementary; exact %). Upper rows: level per policy model (mean ± sample SD over available seeds). Lower rows: larger-policy model minus the K48 model trained on the same seed (common seeds 42–44), with per-seed differences, seed-level 90 % t interval, Holm-corrected Stouffer p of the row-level McNemar tests, and the all-seeds sign rule. Recomputing the 2,000 K48 references under every larger nested policy gives identical executable tuples (0/2,000 conflicts), so utterances and target actions are identical across models. Under the fixed-step budget the shared actions are answered markedly worse by the larger-policy models; under matched exposure the point-estimate gaps at d = 384 narrow (difference of differences on the same seeds: K240 +3.5 pp, 90 % CI [−2.2, +9.3]; K480 +4.0 [−8.5, +16.6]; K960 +12.4 [−2.4, +27.2]) but every three-seed interval includes zero. K48 at d = 256 is under-trained under fixed epochs (596 steps) and is not used for the budget comparison.

| SFT budget | d | policy / contrast | seeds | exact % on K48 test | per-seed Δ pp | mean Δ [90 % CI] | Holm p | all seeds same sign |
|---|---|---|---|---|---|---|---|---|
| fixed steps | 256 | K48 | 3 | 82.9 ± 5.4 |  |  |  |  |
| fixed steps | 256 | K240 | 5 | 76.7 ± 6.6 |  |  |  |  |
| fixed steps | 256 | K480 | 5 | 63.5 ± 5.0 |  |  |  |  |
| fixed steps | 256 | K960 | 5 | 49.5 ± 14.6 |  |  |  |  |
| fixed steps | 384 | K48 | 3 | 89.0 ± 2.1 |  |  |  |  |
| fixed steps | 384 | K240 | 5 | 81.9 ± 5.7 |  |  |  |  |
| fixed steps | 384 | K480 | 3 | 79.8 ± 4.1 |  |  |  |  |
| fixed steps | 384 | K960 | 5 | 70.5 ± 12.5 |  |  |  |  |
| fixed epochs | 256 | K48 | 3 | 68.1 ± 6.1 |  |  |  |  |
| fixed epochs | 256 | K240 | 5 | 76.7 ± 6.6 |  |  |  |  |
| fixed epochs | 256 | K480 | 3 | 72.7 ± 1.6 |  |  |  |  |
| fixed epochs | 256 | K960 | 3 | 76.0 ± 5.5 |  |  |  |  |
| fixed epochs | 384 | K48 | 3 | 85.5 ± 1.5 |  |  |  |  |
| fixed epochs | 384 | K240 | 5 | 81.9 ± 5.7 |  |  |  |  |
| fixed epochs | 384 | K480 | 5 | 81.7 ± 3.5 |  |  |  |  |
| fixed epochs | 384 | K960 | 5 | 80.7 ± 7.3 |  |  |  |  |
| fixed steps | 256 | K240 − K48 | 3 |  | +4.8, -3.9, -13.6 | -4.2 [-19.7, +11.3] | 2.0e-06 | no |
| fixed steps | 256 | K480 − K48 | 3 |  | -15.3, -17.2, -22.4 | -18.3 [-24.6, -12.0] | 0.0e+00 | yes |
| fixed steps | 256 | K960 − K48 | 3 |  | -47.9, -22.2, -38.1 | -36.1 [-57.9, -14.2] | 0.0e+00 | yes |
| fixed steps | 384 | K240 − K48 | 3 |  | -12.7, +1.8, -12.6 | -7.8 [-21.9, +6.2] | 1.3e-15 | no |
| fixed steps | 384 | K480 − K48 | 3 |  | -9.2, -3.2, -15.2 | -9.2 [-19.4, +1.0] | 0.0e+00 | yes |
| fixed steps | 384 | K960 − K48 | 3 |  | -9.5, -32.1, -17.9 | -19.9 [-39.1, -0.6] | 0.0e+00 | yes |
| fixed epochs | 256 | K240 − K48 | 3 |  | +18.9, +9.2, +3.6 | +10.6 [-2.5, +23.6] | 0.0e+00 | yes |
| fixed epochs | 256 | K480 − K48 | 3 |  | +7.5, -1.1, +7.4 | +4.6 [-3.8, +13.0] | 3.0e-09 | no |
| fixed epochs | 256 | K960 − K48 | 3 |  | +6.8, +6.0, +10.8 | +7.9 [+3.5, +12.3] | 0.0e+00 | yes |
| fixed epochs | 384 | K240 − K48 | 3 |  | -9.0, +1.8, -5.8 | -4.3 [-13.7, +5.0] | 1.9e-10 | no |
| fixed epochs | 384 | K480 − K48 | 3 |  | -9.4, -3.5, -2.6 | -5.2 [-11.5, +1.1] | 6.7e-16 | yes |
| fixed epochs | 384 | K960 − K48 | 3 |  | -7.0, -16.4, +1.1 | -7.4 [-22.3, +7.4] | 0.0e+00 | no |

Source: `backend/reports/scale_grid_keff_common48/common48_analysis.json (tools/analyze_keff_common48.py)`
