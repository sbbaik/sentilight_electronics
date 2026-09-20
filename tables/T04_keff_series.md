**T04_keff_series.** K_eff series: exact tuple match for four nested policies across width under two SFT budgets, and the smallest tested d reaching 60 % exact under fixed steps. Seed tiers: the K240 column and the decision cells (fixed steps: K48 d128/192, K480 d192/256, K960 d256/384; matched exposure: K480 and K960 at d384/512) are five-seed cells; all other cells are three-seed screening cells. The 60 % threshold was not specified in advance; it is a descriptive common threshold chosen after the results because all four policies crossed it within the tested width grid (50 % and 70 % in the last row as sensitivity). Each K_eff level is represented by one nested policy, so action-set cardinality is partially confounded with the semantic composition of the added actions. Values are mean ± sample SD (n − 1) across seeds; seed counts are stated in the caption.

| condition | K_eff | d=128 | d=192 | d=256 | d=384 | d=512 | smallest d ≥ 60 % exact |
|---|---|---|---|---|---|---|---|
| fixed steps (≈3,100) | 48 | 67.5 ± 5.2 | 81.0 ± 3.7 | 82.9 ± 5.4 | 89.0 ± 2.1 | 86.0 ± 3.7 | 128 |
| fixed steps (≈3,100) | 240 | 49.5 ± 4.8 | 70.6 ± 5.4 | 78.0 ± 4.0 | 80.8 ± 3.6 | 81.6 ± 5.3 | 192 |
| fixed steps (≈3,100) | 480 | 6.5 ± 1.1 | 54.6 ± 6.5 | 69.6 ± 2.9 | 78.2 ± 4.1 | 79.9 ± 1.0 | 256 |
| fixed steps (≈3,100) | 960 | 0.2 ± 0.1 | 19.1 ± 1.5 | 56.0 ± 13.3 | 69.4 ± 13.2 | 76.1 ± 2.2 | 384 |
| fixed epochs (4) | 48 | 0.0 ± 0.0 | 30.7 ± 7.0 | 68.1 ± 6.1 | 85.5 ± 1.5 | 83.3 ± 8.4 |  |
| fixed epochs (4) | 240 | 49.5 ± 4.8 | 70.6 ± 5.4 | 78.0 ± 4.0 | 80.8 ± 3.6 | 81.6 ± 5.3 |  |
| fixed epochs (4) | 480 | 47.5 ± 9.8 | 71.0 ± 6.3 | 76.5 ± 4.2 | 81.3 ± 4.2 | 78.8 ± 4.0 |  |
| fixed epochs (4) | 960 | 51.3 ± 9.2 | 68.2 ± 3.6 | 74.7 ± 9.5 | 79.9 ± 7.8 | 79.0 ± 9.7 |  |
| fixed steps: log d* vs log K_eff slope |  |  |  |  |  |  | 50%: 0.22; 60%: 0.35 (R² 0.96); 70%: 0.33 |

Source: `backend/reports/scale_grid_keff_fs/keff_analysis.json; scale_grid_keff/keff_analysis_fixed_epochs.json`
