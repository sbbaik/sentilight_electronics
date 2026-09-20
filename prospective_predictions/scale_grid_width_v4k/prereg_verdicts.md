# Closing experiment X — width under the final tokenizer (V = 4k natural, L = 8, five seeds)

- Launched 2026-09-06 08:26, finished 09:37; 15 runs (X224 / X256 / X320 × seeds 42–46), 0 failures. Inputs frozen in `inputs.sha256`; predictions frozen in `config/width_v4k_series.json`.
- Reference: V2 V4k, d = 384, same tokenizer / data / budget, five seeds.
- Question: the action-space analysis placed the width knee at d ≈ 224–256 (K_eff = 240) with the 24k production tokenizer. Does the knee stay there when the input representation is the 4k natural tokenizer that the final model uses?

## Results (exact tuple match %, mean ± SD; per-seed in brackets)

| d | params | emb. share | exact % | coarse % | strict % | per-seed exact |
|--:|--:|--:|--:|--:|--:|---|
| 224 | 5.8M | 16 % | 79.0 ± 2.8 | 86.6 ± 1.6 | 49.5 ± 1.3 | 78.2, 74.6, 79.8, 79.3, 83.2 |
| 256 | 7.3M | 14 % | 76.0 ± 4.4 | 82.6 ± 3.6 | 48.1 ± 1.0 | 72.0, 72.8, 83.5, 78.3, 73.2 |
| 320 | 11.2M | 11 % | 83.8 ± 3.0 | 88.9 ± 2.6 | 51.0 ± 1.4 | 89.6, 83.2, 81.8, 81.0, 83.2 |
| **384** (V2 V4k) | 15.7M | 10 % | **86.5 ± 1.6** | **90.4 ± 1.0** | 51.4 ± 0.6 | 85.2, 86.7, 88.6, 84.3, 87.9 |

Seed-level contrasts (exact tuple; t CI df = 4; hierarchical bootstrap; DerSimonian–Laird):

| contrast | mean Δ pp | 90 % CI (t) | 95 % CI (bootstrap) | seeds agreeing |
|---|--:|---|---|--:|
| X224 → X256 | −3.1 | [−8.1, +2.0] | [−7.4, +1.1] | 1/5 (no gain; if anything a drop) |
| X256 → X320 | +7.8 | [+0.7, +14.9] | [+1.9, +13.6] | 4/5 |
| X320 → 384 | +2.8 | [−1.3, +6.8] | [−1.1, +5.7] | 4/5 |
| **X256 → 384** | **+10.6** | [+6.1, +15.0] | [+6.8, +14.2] | **5/5** |

## Verdicts

| Prediction | Verdict |
|---|---|
| P-X1: X256 within 3 pp of d = 384; X224 → X256 an adopted rise | **Rejected on both parts.** X256 is 10.6 pp below d = 384 with all five seeds agreeing, and X224 → X256 is not a rise. |
| P-X2: SD at X256 ≤ 2 × SD at 384 | **Rejected.** 4.4 vs 1.6 (2.7×); X256 is bimodal across seeds (72–73 vs 78–84). |

## Reading

1. **The width–performance relationship changed substantially with the tokenizer configuration, and no stable plateau was observed below d = 384 under the 4k tokenizer.** With the 24k production tokenizer the curve flattened above d ≈ 256 (W256 78.0 → W384 80.8, +2.8 pp at five seeds). With the 4k natural tokenizer the same step is +10.6 pp. Whether the curve keeps rising beyond 384 is untested (d = 512 not run under 4k), and X320 → 384 (+2.8 pp, 90 % CI [−1.3, +6.8]) is neither a confirmed gain nor a confirmed ±3 pp equivalence. The K_eff-derived knee (d ≈ K_eff) held for the tokenizer it was measured with, not for the final one. The 4k curve is also non-monotonic (X224 ≥ X256, difference not significant), so it should not be described as a smooth knee.
2. **Tokenizer–width interaction (result) and its mechanism (hypothesis).** The width effect 384 − 256 is +10.6 pp under the 4k tokenizer and +2.8 pp under the 24k tokenizer; the interaction is +7.8 pp on average but its seed-level 90 % CI includes zero (addendum below), so it is reported as suggestive. Because the two tokenizers differ in training corpus and provenance as well as size, this is a *tokenizer-configuration* × width interaction, not a pure vocabulary-size effect. The longer sequences produced by the 4k tokenizer (216 vs 159 tokens) are consistent with a shift of compositional burden from the embedding table to the Transformer blocks; that shift is a plausible explanation, not a measured one.
3. **Consequence for the paper's central claim.** K_eff is not a lower bound in any strict sense (X224 < K_eff scored 79.0 %, above X256), so it should be called a *task-based search prior* (a starting region for the width search), not a bound or a risk boundary: configurations well below it (d = 128–192) were poor under the 24k tokenizer only (not run under 4k), and configurations near it were seed-unstable under both. Where performance stabilises is set by tokenizer configuration, exposure and budget, not by K_eff. The paper's contribution therefore shifts from closed-form model-size prediction to **action-space-informed capacity search**: use K_eff to choose where to start and which widths to evaluate, then evaluate the candidate region and larger widths with multiple seeds and choose on accuracy, variance and deployment cost together. The stronger statement "the predicted-knee model became the final model" is **not** supported: the 7.3M knee model loses 10.6 pp.
4. **Final model unchanged: V2 V4k, d = 384, L = 8, V = 4k, 15.7M** — the most accurate and most stable cell (SD 1.6). This is a conservative engineering choice, not a statistical win over X320 (11.2M, 83.8 ± 3.0; −2.8 pp, 90 % CI [−1.3, +6.8], TOST ±3 fails on the upper side). X320 is a *parameter-efficient alternative* (29 % fewer parameters; not yet quantized or CPU-benchmarked, so not a deployment claim); X224 (5.8M, 79.0 %) is an ultra-small Pareto point, and X256 (7.3M, 76.0 ± 4.4) is dominated by X224 on both mean and variance. d = 384 was selected conservatively because it achieved the highest mean accuracy and the lowest seed variance among the tested 4k configurations.
5. **Boundary instability again.** X256's bimodal seeds repeat the pattern seen at W224 (three seeds), K960 d = 256 and C4kL4: configurations near the estimated starting region were repeatedly seed-sensitive; the recipe therefore evaluates the candidate region *and* larger widths with multiple seeds rather than adopting the region's edge. No fixed multiplier is claimed.

## Caveats
- One depth (L = 8) and one budget (2,400 steps); at a larger budget the 4k knee may move back left (rare-token exposure is not the issue at 4k, but composition capacity may still be trainable with more steps).
- X224 uses head_dim 56 (4 heads); it is not the cause of the X256 dip (X256 uses head_dim 64).

## Addendum (2026-09-06): requested analyses (values as computed from per-row files, five seeds)
- **Tokenizer-configuration × width interaction** (exact tuple, 2×2 cells W256/W384/X256/V384): width effect 384 − 256 per seed under the 4k tokenizer [+13.2, +13.9, +5.0, +6.0, +14.7] vs under the 24k tokenizer [−3.5, −2.2, +3.8, +12.6, +3.1]; interaction per seed [+16.7, +16.2, +1.2, −6.6, +11.7], mean **+7.8 pp**, 90 % t-CI [−1.9, +17.5], 95 % [−4.8, +20.5], hierarchical bootstrap 95 % [−0.4, +15.6]; 4/5 seeds positive. **The interaction is suggestive, not established at the seed level** (the 24k width effect is dominated by W384 seed 45's unusually high score). Report as "the width effect was larger under the 4k tokenizer in four of five seeds (mean +7.8 pp; seed-level CI includes zero)".
- **384 vs X320**: +2.8 pp, 90 % CI [−1.3, +6.8]; neither superiority nor ±3 pp equivalence is established.
- **X256 vs X224**: −3.1 pp, 90 % CI [−8.1, +2.0]; not significant. The 4k curve's non-monotonicity is within seed noise.
- Note: an earlier version of this addendum contained placeholder numbers written before the computation; they were replaced with the computed values above on the same day.

## Addendum 2 (2026-09-06): paired vs unpaired sensitivity of the interaction, and seeding
- **Seeding check (code):** `pretrain_from_scratch.py` and `finetune_from_pretrain.py` call `random.seed / np.random.seed / torch.manual_seed(seed)` once at start. The SFT data order is therefore identical across configurations with the same seed and the same data (a paired element), but parameter initialisation draws depend on tensor shapes, so runs with different width or vocabulary are **not** common-random-number replicates. Same-numbered seeds are partially paired; both analyses are reported.
- **Interaction (V384 − X256) − (W384 − W256):** paired seed-level 90 % t-CI [−1.9, +17.5]; unpaired Welch (df 12.5) 90 % CI [+1.9, +13.8], t = 2.34; permutation test over seed labels within tokenizer (20,000 permutations) two-sided p = 0.106. Verdict unchanged: **suggestive, not established**. Report as "the width effect was larger under the 4k tokenizer in four of five seeds (mean +7.8 pp); the seed-level confidence interval includes zero".
- **384 vs X320:** paired 90 % CI [−1.3, +6.8]; unpaired Welch (df 6.1) [−0.4, +6.0]. Neither superiority nor ±3 pp equivalence is established under either analysis.
- Naming: *tokenizer-configuration × width interaction* (the two tokenizers differ in corpus and provenance as well as size); never "vocabulary-size × width".
- Files: `interaction_sensitivity.json`.
