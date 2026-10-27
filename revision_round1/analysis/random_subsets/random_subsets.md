# Random-subset policies: action count with composition fixed

nested random subsets of the 240 production cells, all categories kept, K240 exposure per cell; pretraining = W-series pretraining checkpoints of the original grid (24k tokenizer; not in the v1.0.0 record); SFT recipe unchanged.

## Exact % on the common K48r test (369 rows, gold identical for every policy)

| schedule | d | K48r | K96r | K144r | K240 |
|---|--:|--:|--:|--:|--:|
| matched | 256 | 81.7 ± 5.1 (3s) | 87.7 ± 4.0 (3s) | 84.4 ± 3.6 (3s) | 77.9 ± 6.7 (5s) |
| matched | 384 | 90.8 ± 1.9 (5s) | 87.8 ± 2.0 (5s) | 86.4 ± 2.0 (5s) | 79.1 ± 3.5 (5s) |
| fixed | 256 | 90.5 ± 3.9 (3s) | 87.1 ± 3.4 (3s) | 84.4 ± 2.4 (3s) | 77.9 ± 6.7 (5s) |
| fixed | 384 | 92.1 ± 1.9 (5s) | 89.2 ± 1.9 (5s) | 88.4 ± 2.0 (5s) | 79.1 ± 3.5 (5s) |

## Exact % on the policy's own test rows

| schedule | d | K48r | K96r | K144r | K240 |
|---|--:|--:|--:|--:|--:|
| matched | 256 | 81.7 ± 5.1 (3s) | 85.8 ± 2.6 (3s) | 83.1 ± 2.7 (3s) | 78.0 ± 4.0 (5s) |
| matched | 384 | 90.8 ± 1.9 (5s) | 88.6 ± 2.3 (5s) | 87.2 ± 2.5 (5s) | 80.8 ± 3.6 (5s) |
| fixed | 256 | 90.5 ± 3.9 (3s) | 86.6 ± 4.1 (3s) | 83.7 ± 1.7 (3s) | 78.0 ± 4.0 (5s) |
| fixed | 384 | 92.1 ± 1.9 (5s) | 89.9 ± 1.5 (5s) | 88.8 ± 2.7 (5s) | 80.8 ± 3.6 (5s) |

## Paired seed differences on the common test (percentage points, 90% and 95% t intervals, seeds favouring the smaller policy; ✓rule = both intervals exclude zero, the paper's superiority rule)

| contrast | matched d256 | matched d384 | fixed d256 | fixed d384 |
|---|--:|--:|--:|--:|
| K48r − K240 | +0.7 90% [-3.9, +5.3] 95% [-6.0, +7.5] (1/3) | +11.8 90% [+7.9, +15.7] 95% [+6.7, +16.9] (5/5) ✓rule | +9.6 90% [+0.2, +19.0] 95% [-4.3, +23.4] (3/3) | +13.0 90% [+9.8, +16.2] 95% [+8.9, +17.1] (5/5) ✓rule |
| K96r − K240 | +6.8 90% [-1.6, +15.1] 95% [-5.5, +19.1] (3/3) | +8.7 90% [+5.5, +11.8] 95% [+4.6, +12.8] (5/5) ✓rule | +6.1 90% [-5.5, +17.8] 95% [-11.0, +23.3] (3/3) | +10.1 90% [+6.2, +14.0] 95% [+5.0, +15.2] (5/5) ✓rule |
| K144r − K240 | +3.4 90% [-4.0, +10.8] 95% [-7.5, +14.3] (2/3) | +7.4 90% [+2.5, +12.3] 95% [+1.0, +13.8] (4/5) ✓rule | +3.4 90% [-7.6, +14.5] 95% [-12.9, +19.7] (2/3) | +9.3 90% [+4.6, +14.1] 95% [+3.2, +15.5] (5/5) ✓rule |
| K48r − K144r | -2.7 90% [-10.1, +4.6] 95% [-13.5, +8.1] (1/3) | +4.4 90% [+1.6, +7.2] 95% [+0.8, +8.0] (5/5) ✓rule | +6.1 90% [-3.6, +15.8] 95% [-8.1, +20.4] (2/3) | +3.7 90% [+0.5, +6.8] 95% [-0.4, +7.8] (4/5) |

## Three independent draws at d = 384 (five seeds; each draw on its own common K48r test)

three independent draws of the nested subsets (seeds 20261023, 20261027, 20261028), d = 384, five seeds, each scored on its own common K48r test; K240 = the same W-series checkpoints scored on each draw's common test.

| schedule | draw | common rows | K48r | K96r | K144r | K240 | K48r − K240 (90%; 95%; seeds) |
|---|--:|--:|--:|--:|--:|--:|---|
| fixed | 1 | 369 | 92.1 ± 1.9 | 89.2 ± 1.9 | 88.4 ± 2.0 | 79.1 ± 3.5 | +13.0 [+9.8, +16.2]; [+8.9, +17.1]; 5/5 ✓rule |
| fixed | 2 | 417 | 95.9 ± 2.0 | 90.6 ± 2.5 | 87.2 ± 3.2 | 82.1 ± 5.3 | +13.8 [+9.4, +18.2]; [+8.0, +19.5]; 5/5 ✓rule |
| fixed | 3 | 400 | 88.6 ± 2.0 | 85.6 ± 2.9 | 86.0 ± 2.7 | 81.4 ± 3.1 | +7.2 [+4.6, +9.8]; [+3.8, +10.6]; 5/5 ✓rule |
| matched | 1 | 369 | 90.8 ± 1.9 | 87.8 ± 2.0 | 86.4 ± 2.0 | 79.1 ± 3.5 | +11.8 [+7.9, +15.7]; [+6.7, +16.9]; 5/5 ✓rule |
| matched | 2 | 417 | 94.4 ± 0.4 | 90.7 ± 2.5 | 87.7 ± 1.2 | 82.1 ± 5.3 | +12.3 [+7.0, +17.6]; [+5.4, +19.2]; 5/5 ✓rule |
| matched | 3 | 400 | 86.0 ± 1.9 | 85.5 ± 2.6 | 86.8 ± 1.9 | 81.4 ± 3.1 | +4.6 [+1.1, +8.1]; [+0.1, +9.1]; 5/5 ✓rule |

Averaged over the three draws, per seed (paired t over five seeds):

| schedule | contrast | mean | 90% | 95% | seeds | draw means | draws meeting the rule |
|---|---|--:|---|---|--:|---|--:|
| matched | K48r-K240 | +9.6 | [+5.8, +13.3] | [+4.7, +14.4] | 5/5 | +11.8, +12.3, +4.6 | 3/3 |
| matched | K96r-K240 | +7.1 | [+3.6, +10.7] | [+2.5, +11.7] | 5/5 | +8.7, +8.6, +4.0 | 3/3 |
| matched | K144r-K240 | +6.1 | [+2.1, +10.1] | [+0.9, +11.4] | 4/5 | +7.4, +5.6, +5.4 | 3/3 |
| fixed | K48r-K240 | +11.3 | [+8.4, +14.3] | [+7.5, +15.2] | 5/5 | +13.0, +13.8, +7.2 | 3/3 |
| fixed | K96r-K240 | +7.6 | [+4.7, +10.5] | [+3.8, +11.4] | 5/5 | +10.1, +8.4, +4.2 | 3/3 |
| fixed | K144r-K240 | +6.4 | [+3.1, +9.6] | [+2.1, +10.6] | 5/5 | +9.3, +5.1, +4.7 | 3/3 |
