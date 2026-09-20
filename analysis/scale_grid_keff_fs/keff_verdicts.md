# K_eff series — results and verdicts (2026-09-05)

Four nested policies (K48 ⊂ K240 ⊂ K480 ⊂ K960), width grid d ∈ {128, 192, 256, 384, 512}, L = 8,
V = 24k, seeds 42/43/44, shared W-series pretrain checkpoints (2,400 steps, clean corpus). Each policy
is fine-tuned on its own policy-only + coverage-fill data and evaluated on its own 2,000-row test set
(every reachable tuple ≥ 2 rows, no conflicting-gold inputs). K240 = the W series. 0 failed tasks in
either condition. Primary metric: exact tuple match (strict is not comparable across policies because
the emotion-constraint clauses exist only for the five production emotions).

## Two training-budget conditions

| Condition | SFT budget | Steps (K48 / K240 / K480 / K960) | Reports |
|---|---|---|---|
| A. fixed epochs (4) | equal exposure per tuple (~200 rows/tuple × 4) | 596 / 3,072 / ≈6,250 / ≈12,770 | `scale_grid_keff/` |
| B. fixed steps (≈3,100) | fixed step / token-position budget (K48 21 ep, K480 2 ep, K960 1 ep) | 3,129 / 3,072 / 3,124 / 3,192 | `scale_grid_keff_fs/` |

## B. Fixed steps — exact tuple match (%, mean ± SD)

| K_eff | d=128 | d=192 | d=256 | d=384 | d=512 |
|--:|--:|--:|--:|--:|--:|
| 48 | 68.2 ± 1.2 | 82.0 ± 1.1 | 82.9 ± 4.4 | 89.0 ± 1.7 | 86.0 ± 3.0 |
| 240 | 52.7 ± 2.3 | 73.6 ± 2.8 | 79.7 ± 3.6 | 79.1 ± 1.3 | 83.7 ± 4.8 |
| 480 | 6.5 ± 0.9 | 58.2 ± 4.4 | 68.5 ± 2.6 | 78.2 ± 3.4 | 79.9 ± 0.8 |
| 960 | 0.2 ± 0.1 | 19.1 ± 1.2 | 55.5 ± 14.1 | 67.7 ± 11.5 | 76.1 ± 1.8 |

Smallest d reaching a level (exact): 

| K_eff | ≥ 50% | ≥ 60% | ≥ 70% |
|--:|--:|--:|--:|
| 48 | 128 | 128 | 192 |
| 240 | 128 | 192 | 192 |
| 480 | 192 | 256 | 384 |
| 960 | 256 | 384 | 512 |

log d* vs log K_eff slope: 0.23 (50%), 0.35 (60%, R² 0.96), 0.33 (70%). A slope of 1 would be d* ∝ K_eff.

## A. Fixed epochs — exact tuple match (%, mean ± SD)

| K_eff | d=128 | d=192 | d=256 | d=384 | d=512 |
|--:|--:|--:|--:|--:|--:|
| 48 | 0.0 ± 0.0 | 30.7 ± 5.7 | 68.1 ± 5.0 | 85.5 ± 1.2 | 83.3 ± 6.9 |
| 240 | 52.7 ± 2.3 | 73.6 ± 2.8 | 79.7 ± 3.6 | 79.1 ± 1.3 | 83.7 ± 4.8 |
| 480 | 47.5 ± 8.0 | 71.0 ± 5.2 | 76.5 ± 3.4 | 78.8 ± 2.0 | 80.9 ± 1.9 |
| 960 | 51.3 ± 7.5 | 68.2 ± 3.0 | 74.7 ± 7.8 | 75.6 ± 5.9 | 85.2 ± 3.6 |

Knee slopes here are ≈ 0 or negative (−0.20 … +0.10): with exposure matched, K240/480/960 lie on
one curve for d ≥ 192, and K48's collapse at d = 128 is under-training (596 steps; best val loss 0.487
vs 0.033 for K240).

## Verdicts

1. **The knee moves with K_eff under a fixed step budget, but sub-linearly.** d* ∝ K_eff^0.23–0.35 on
   exact match (levels 50–70%). The a-priori heuristic d ≳ K_eff (slope 1) is too strong; a
   4× larger action space needed roughly 1.5–2× the width for the same accuracy, not 4×.
2. **K_eff acts mainly through training budget, not width.** When every tuple receives the same
   exposure (condition A), the K_eff dependence of accuracy almost disappears for d ≥ 192: the 240,
   480 and 960 columns are within seed noise of each other. What a larger K_eff demands is more
   optimisation steps (∝ K_eff at fixed rows per tuple), not proportionally more hidden units.
3. **Small widths fail catastrophically only when both K_eff is large and compute is fixed**
   (K960, d = 128: 0.2%; K480, d = 128: 6.5%). This is the regime the sizing recipe must warn about:
   at a fixed step budget the width floor rises with K_eff.
4. **Seed instability concentrates at the knee.** K960 SD is 14.1 at d = 256 and 11.5 at d = 384,
   and W224 in the W series had SD 6.6: widths just at the edge of sufficiency train unreliably.
   A practical margin above d* is therefore warranted.
5. **Strict is capped by the metric, not capacity** (K240 ≈ 50%, K48 ≈ 72%, K960 ≈ 72%), and
   coarse saturates near 88–93%. Exact tuple match should be the headline metric in the paper.

## Implications for the paper's recipe (Section 3.3)

- Replace "d ≳ K_eff" by an empirical rule of the form d* ≈ c · K_eff^α with α ≈ 0.3 at a fixed
  step budget, and state the budget explicitly (steps per tuple). "Fixed steps" is not fixed FLOPs: wider models and larger LM heads cost more per step.
- Add a data/compute step: total SFT steps must grow ≈ linearly with K_eff to keep per-tuple
  exposure constant; if the step budget is fixed, widen instead.
- Keep the shoulder framing from the W series: above d*, returns flatten within seed noise.

## Caveats

- Depth (L = 8), d_ff ratio and pretraining budget were fixed; the α estimate is for width only.
- Test sets differ per policy (each policy's own reachable set), so absolute levels across columns
  are comparable only because every test set covers all its tuples with the same templates.
- Condition B gives K960 a single epoch, so its small-d models are also under-exposed per tuple;
  conditions A and B bracket the two natural budget definitions rather than settling on one.
- New emotions have no strict-constraint clauses; new colours have no morphological adjective rows.
