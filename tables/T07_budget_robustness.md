**T07_budget_robustness.** Pretraining budget doubled from 2,400 to 4,800 steps for the 4k and 24k natural-corpus tokenizers (d = 384, L = 8, three seeds). The corpus is repeated, not enlarged. Values are mean ± sample SD (n − 1) across seeds; seed counts are stated in the caption.

| tokenizer | exact % @2,400 | exact % @4,800 | Δ exact pp | coarse % @2,400 | coarse % @4,800 |
|---|---|---|---|---|---|
| 4k natural | 86.5 ± 1.8 | 85.9 ± 1.6 | -0.7 | 90.4 ± 1.1 | 89.9 ± 1.3 |
| 24k natural | 68.2 ± 7.5 | 70.6 ± 4.7 | +2.4 | 78.3 ± 5.7 | 80.4 ± 2.2 |
| gap 4k − 24k | +18.6 | +15.3 |  |  |  |

Source: `backend/reports/scale_grid_budget/*; scale_grid_vocab_natural/*`
