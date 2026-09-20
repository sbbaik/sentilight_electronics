**T05_depth_series.** Depth series (d = 384, V = 24k production tokenizer) for the production policy (A = 3) and the attribute-count control policy (A = 2, intensity fixed neutral, K_eff 192). L = 2, 3, 4 are on five common seeds (42–46) in both policies; L ≥ 6 on three. L = 2 could not provide consistently reliable performance across the two policy variants: L = 2 → 4 is +12.6 pp at A = 2 (5/5 seeds; 90 % t CI [+3.3, +22.0], hierarchical-bootstrap 95 % CI [+5.7, +21.1]) and +4.4 pp at A = 3 (4/5; 90 % CI [+0.2, +8.5]), with two A = 2 seeds at L = 2 generalising poorly (65.5 %, 59.2 %). Whether the gain arises between L = 2 and 3 or between 3 and 4 was not resolved (no single adjacent step adopted at five seeds; policy × depth interactions imprecise), so attribute count was not used as a depth-sizing rule. Under this tokenizer and width no reliable adjacent gain was detected above L = 4, although equivalence among deeper configurations was not established. L = 8 at A = 3 is bit-identical to W384 (five seeds 80.8 ± 3.6). Absolute levels are not comparable across policies. Values are mean ± sample SD (n − 1) across seeds; n is given in the seeds column.

| policy | L | parameters | seeds | exact tuple % | coarse % | strict % | latency ms |
|---|---|---|---|---|---|---|---|
| A=3, K_eff 240 (production) | 2 | 12,756,864 | 5 | 77.3 ± 2.3 | 83.3 ± 1.8 | 46.4 ± 1.6 | 68 |
| A=3, K_eff 240 (production) | 3 | 14,527,104 | 5 | 78.2 ± 1.7 | 83.5 ± 1.7 | 47.0 ± 0.8 | 91 |
| A=3, K_eff 240 (production) | 4 | 16,297,344 | 5 | 81.7 ± 4.9 | 86.1 ± 3.3 | 48.8 ± 1.2 | 118 |
| A=3, K_eff 240 (production) | 6 | 19,837,824 | 3 | 80.3 ± 4.5 | 84.7 ± 3.8 | 48.5 ± 1.5 | 163 |
| A=3, K_eff 240 (production) | 8 | 23,378,304 | 3 | 79.1 ± 1.6 | 84.9 ± 0.7 | 49.3 ± 0.2 | 216 |
| A=3, K_eff 240 (production) | 12 | 30,459,264 | 3 | 79.4 ± 1.4 | 84.8 ± 2.2 | 48.4 ± 1.3 | 314 |
| A=3, K_eff 240 (production) | 16 | 37,540,224 | 3 | 73.2 ± 9.6 | 81.0 ± 7.8 | 46.9 ± 3.7 | 420 |
| A=2, K_eff 192 (control) | 2 | 12,756,864 | 5 | 72.3 ± 9.9 | 77.5 ± 7.9 | 66.9 ± 6.1 | 68 |
| A=2, K_eff 192 (control) | 3 | 14,527,104 | 5 | 81.0 ± 5.8 | 84.2 ± 4.8 | 71.9 ± 2.8 | 92 |
| A=2, K_eff 192 (control) | 4 | 16,297,344 | 5 | 84.9 ± 5.4 | 87.6 ± 3.8 | 74.9 ± 2.0 | 116 |
| A=2, K_eff 192 (control) | 6 | 19,837,824 | 3 | 83.1 ± 4.1 | 86.7 ± 2.8 | 73.6 ± 2.3 | 165 |
| A=2, K_eff 192 (control) | 8 | 23,378,304 | 3 | 86.5 ± 2.5 | 90.1 ± 1.1 | 76.8 ± 0.9 | 209 |

Source: `backend/reports/scale_grid_depth{,_l3}/width_analysis.json; scale_grid_depth_a2{,_l3}/width_analysis.json`
