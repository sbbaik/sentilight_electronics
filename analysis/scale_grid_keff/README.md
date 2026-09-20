# K_eff series — two training-budget conditions

- `scale_grid_keff/<P>/` — **fixed epochs (4)**. Optimiser steps therefore scale with policy size:
  K48 ≈ 600, K240 ≈ 3,070 (W series), K480 ≈ 6,250, K960 ≈ 12,770. K48 is under-trained at small
  widths (best val loss 0.487 at d=128 vs 0.033 for K240), so this condition confounds K_eff with
  training budget. Kept as the "equal exposure per tuple" condition.
- `scale_grid_keff_fs/<P>/` — **fixed steps (≈3,100)**: K48 21 epochs, K480 2 epochs, K960 1 epoch,
  K240 = W series (4 epochs). Step-matched like the pretraining stage. Primary condition for the
  K_eff-vs-knee analysis.
Both use the same W-series pretrain checkpoints, seeds 42/43/44, d ∈ {128,192,256,384,512}.
