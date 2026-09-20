# L = 3 addition to the depth series — verdicts (A = 3 K240 and A = 2 A2K192)

- D3 pretrain checkpoints (d 384, L 3, 24k, 2,400 steps) at seeds 42–46, shared by both policies; SFT 4 epochs; eval 2,000-row test_rule per policy (25 runs). Seed fill 2026-09-06 (config/depth_seed_fill.json, 14 runs) added seeds 45, 46 to A3 L2, A2 L2 and A2 L4, so L2/L3/L4 are on five common seeds in both policies. Three-paired-seed results are preserved in depth_l3_analysis_3paired_seeds.json.
- SD below is the sample SD (n−1).

## Exact tuple match % (per seed; mean ± SD)

| Policy | L | Seeds | Per seed | Mean ± SD | 90% t CI |
|---|--:|--:|---|--:|---|
| A3 | 2 | 5 | 74.7 / 78.8 / 78.8 / 75.0 / 79.5 | 77.3 ± 2.3 | [75.1, 79.5] |
| A3 | 3 | 5 | 76.7 / 79.2 / 77.2 / 80.8 / 77.3 | 78.2 ± 1.7 | [76.6, 79.9] |
| A3 | 4 | 5 | 84.8 / 85.2 / 81.8 / 73.2 / 83.3 | 81.7 ± 4.9 | [77.0, 86.3] |
| A2 | 2 | 5 | 80.7 / 82.3 / 73.6 / 65.5 / 59.2 | 72.3 ± 9.9 | [62.8, 81.7] |
| A2 | 3 | 5 | 73.6 / 85.4 / 76.0 / 84.8 / 85.5 | 81.0 ± 5.8 | [75.5, 86.6] |
| A2 | 4 | 5 | 86.5 / 91.4 / 77.7 / 81.4 / 87.5 | 84.9 ± 5.4 | [79.8, 90.0] |

## Steps (row-level McNemar per seed, Stouffer, Holm over 18, all-seeds sign rule; paired seeds per policy: A3 [42, 43, 44, 45, 46], A2 [42, 43, 44, 45, 46])

| Policy | Step | Metric | Mean Δ pp | Stouffer z | Holm p | Signs | Adopted |
|---|---|---|--:|--:|--:|---|---|
| A3 | D2->D3 | strict | +0.64 | +1.79 | 2.06e-01 | ✗ | no |
| A3 | D2->D3 | coarse | +0.21 | +0.46 | 6.45e-01 | ✗ | no |
| A3 | D2->D3 | exact | +0.92 | +1.82 | 2.06e-01 | ✗ | no |
| A3 | D3->D4 | strict | +1.76 | +5.51 | 1.41e-07 | ✗ | no |
| A3 | D3->D4 | coarse | +2.63 | +6.43 | 6.30e-10 | ✗ | no |
| A3 | D3->D4 | exact | +3.43 | +7.79 | 8.66e-14 | ✗ | no |
| A3 | D2->D4 | strict | +2.40 | +6.60 | 2.54e-10 | ✓ | **yes** |
| A3 | D2->D4 | coarse | +2.84 | +6.62 | 2.44e-10 | ✗ | no |
| A3 | D2->D4 | exact | +4.35 | +8.67 | 0.00e+00 | ✗ | no |
| A2 | D2->D3 | strict | +5.00 | +7.48 | 9.06e-13 | ✗ | no |
| A2 | D2->D3 | coarse | +6.62 | +6.65 | 2.28e-10 | ✗ | no |
| A2 | D2->D3 | exact | +8.78 | +6.89 | 5.69e-11 | ✗ | no |
| A2 | D3->D4 | strict | +3.06 | +7.95 | 2.49e-14 | ✓ | **yes** |
| A2 | D3->D4 | coarse | +3.44 | +7.24 | 4.93e-12 | ✗ | no |
| A2 | D3->D4 | exact | +3.85 | +6.81 | 8.86e-11 | ✗ | no |
| A2 | D2->D4 | strict | +8.06 | +14.18 | 0.00e+00 | ✓ | **yes** |
| A2 | D2->D4 | coarse | +10.06 | +14.18 | 0.00e+00 | ✓ | **yes** |
| A2 | D2->D4 | exact | +12.63 | +14.81 | 0.00e+00 | ✓ | **yes** |

## Seed level (exact)

- A3: D4−D2 per seed [10.0, 6.5, 3.0, -1.7, 3.9], mean +4.35, 90% CI [+0.2, +8.5].
- A3: D3−D2 per seed [2.0, 0.5, -1.6, 5.8, -2.1], mean +0.92, 90% CI [-2.1, +4.0]; D4−D3 per seed [8.0, 6.0, 4.6, -7.5, 6.0], mean +3.43, 90% CI [-2.5, +9.4], TOST ±3 pp p = 0.557; D4 (5 seeds) − D3 (5 seeds) Welch +3.43, 90% CI [-1.2, +8.1], p = 0.199.
- A2: D4−D2 per seed [5.8, 9.1, 4.1, 15.9, 28.2], mean +12.63, 90% CI [+3.3, +22.0].
- A2: D3−D2 per seed [-7.1, 3.1, 2.4, 19.2, 26.3], mean +8.78, 90% CI [-4.2, +21.8]; D4−D3 per seed [13.0, 6.0, 1.8, -3.3, 1.9], mean +3.85, 90% CI [-1.9, +9.6], TOST ±3 pp p = 0.615; D4 (5 seeds) − D3 (5 seeds) Welch +3.85, 90% CI [-2.7, +10.4], p = 0.308.

## Interaction (Welch on per-seed differences over the paired seeds)

- (D4-D3)_A3 - (D4-D3)_A2: -0.42 pp, 90% CI [-7.7, +6.8], df 8.0, p = 0.917
- (D3-D2)_A3 - (D3-D2)_A2: -7.86 pp, 90% CI [-20.9, +5.1], df 4.4, p = 0.272

## Verdicts (pre-registered in `config/depth_l3_series.json`)

| Prediction | Verdict |
|---|---|
| P-L3-1 (L = A + 1 holds) | **not supported** |
| P-L3-2 (depth requirement not attribute-linked) | **inconclusive: relative position of L = 3 differed descriptively, between-policy difference statistically inconclusive** |
| P-L3-3 (L = 3 sufficient for both) | **supported by the adoption rule only (D4−D3 means positive, CIs include 0, TOST fails: sufficiency not established)** |

D3 position relative to D2/D4 (exact): A3 = D2-level, A2 = intermediate.

## Reading (five common seeds, after the seed fill)
- No adjacent exact step between L = 2 and L = 4 is adopted in either policy at five seeds: every step has one dissenting seed (A3 D3→D4 and D2→D4: seed 45 D4 = 73.2 %; A2 D2→D3: seed 42; A2 D3→D4: seed 45).
- Over the whole span L = 2 → 4: at A = 2 the gain is adopted (+12.6 pp, 5/5 seeds; paired-seed 90% t CI [+3.3, +22.0], 95% [+0.4, +24.8]; sensitivity: hierarchical bootstrap 95% [+5.7, +21.1], DL pooled [+4.8, +20.4]). At A = 3 a mean improvement was also observed (+4.4 pp) but one seed ran the other way (4/5) and the inference is sensitive to the interval method and confidence level (paired-seed 90% t CI [+0.2, +8.5] excludes 0, 95% t CI [−1.0, +9.7] includes it; bootstrap and DL exclude it). The primary analysis is the paired-seed difference with its t interval (five independent training replicates); bootstrap and DL are sensitivity analyses.
- L = 2 could not provide consistently reliable performance across the tested policy variants: stable at A = 3 (77.3 ± 2.3) but two of five A = 2 seeds generalised poorly (65.5 %, 59.2 %) despite normal training and validation loss. Failure signature (scale_grid_depth_a2/D2_seed_instability.md): no output-mode collapse (179/158 distinct in-policy tuples of 192, zero JSON errors, out-of-policy rows 1.7/4.2 %), errors concentrated in anger and boredom (13–48 % vs 69–90 % at other seeds, whole-tuple errors) and recovered at L = 4 — suggesting seed-sensitive difficulty with the policy's emotion-conditioned tuples at L = 2, without establishing a mechanism. L = 2 is therefore not recommended as a default depth; it is not shown to be universally insufficient.
- Where within L = 2..4 the gain lies is not resolved at five seeds: at A = 3 it sits mostly in L = 3 → 4 (+3.4 vs +0.9), at A = 2 mostly in L = 2 → 3 (+8.8 vs +3.9), but the (D3−D2) interaction is −7.9 pp with 90% CI [−20.9, +5.1] and the (D4−D3) interaction −0.4 pp, CI [−7.7, +6.8]. The three-seed statement 'largest gain between L = 3 and L = 4 in both policies' did not survive the seed fill.
- L = A + 1 (L = 3 sufficient at A = 2): not supported by the pre-registered rule (D2→D3 at A = 2 not adopted; interaction CI includes 0). The data are compatible both with no attribute-linked shift and with a modest shift in the direction of the heuristic; neither is established.
- P-L3-3: sufficiency of L = 3 was not established. The adoption rule is met only by the letter (D3→D4 not adopted in either policy). D4−D3 is +3.4 / +3.9 pp with CIs including 0 and TOST ±3 pp fails in both, so 'L = 3 sufficient' is not established; report as no reliable adjacent gain detected, not as sufficiency.
- Under the 24k tokenizer and d = 384, no reliable adjacent gain was observed above L = 4 (D series, three seeds above L = 4); equivalence of L = 4 with deeper models is not established.
- Caveats: two policies differing also in K_eff, factor cardinality and SFT step count (2,476 vs 3,072 at matched per-tuple exposure); one width, one tokenizer, one budget; depth effects in this range are of the same order as seed-to-seed spread.
