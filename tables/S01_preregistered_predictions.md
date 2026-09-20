**S01_preregistered_predictions.** Prospectively specified predictions and their verdicts (supplementary). Predictions were written and recorded internally, with SHA-256 hashes of the inputs, before each series ran (no external time-stamped registry); rejected predictions are reported unchanged. Values are mean ± sample SD (n − 1) across seeds; seed counts are stated in the caption.

| series | prediction | as written | verdict | record |
|---|---|---|---|---|
| W (width, 24k) | P-W1 | coarse rises steeply W128→W256; largest step at W224→W256 | met at five seeds (W192 = W224 = 70.6; W224→W256 +7.4 pp adopted) | scale_grid_width/prereg_verdicts.md; scale_grid_combo/five_seed_verdicts.md |
| W | P-W2 | above W256 every step gains less than W224→W256 | met | scale_grid_width/prereg_verdicts.md |
| W | P-W3 | W384 ≥ IoTJ Gen-Policy 23M | met (plausibility check) | scale_grid_width/prereg_verdicts.md |
| K (K_eff) | P1 (pre-registered rule) | 8M→23M and 23M→60M both < 3.5 pp ⇒ saturation | not used; replaced by d* vs K_eff analysis: slope 0.23–0.35 under fixed steps, ≈0 under fixed epochs | scale_grid_keff_fs/keff_verdicts.md |
| D (depth) | P-D1 | D2→D4 and D4→D6 adopted rises | half met (D2→D4 only; peak at L = 4) | scale_grid_depth/prereg_verdicts.md |
| D | P-D2 | no adopted gain above D8 | met | scale_grid_depth/prereg_verdicts.md |
| D | P-D3 | D8 reproduces W384 within 3 pp | met exactly (bit-identical) | scale_grid_depth/prereg_verdicts.md |
| V (vocabulary, natural) | P-V1 | flat from V8k to V24k | rejected (monotone decline) | scale_grid_vocab_natural/prereg_verdicts.md |
| V | P-V2 | V4k not worse than V8k | met and inverted (V4k better) | scale_grid_vocab_natural/prereg_verdicts.md |
| V | P-V3 | retrained V24k ≥ production 24k | rejected (−10.9 pp) | scale_grid_vocab_natural/prereg_verdicts.md |
| V | P-V4 | natural-corpus tokenizer beats template-corpus tokenizer at every size | met | scale_grid_vocab_natural/prereg_verdicts.md |
| C (d384 L4 V4k) | P-C1 | within 3 pp of d384 L8 V4k | met at three seeds; at five seeds −4.6 pp (4/5 seeds), not equivalent | scale_grid_combo/prereg_verdicts.md; five_seed_verdicts.md |
| C | P-C2 | latency ≈ half of L8 | met | scale_grid_combo/prereg_verdicts.md |
| C | P-C3 | depth and vocabulary effects additive | rejected | scale_grid_combo/prereg_verdicts.md |
| B (budget) | P-B1 | 24k gains ≥ 3 pp more than 4k from doubling steps | met narrowly (gain itself seed-split) | scale_grid_budget/prereg_verdicts.md |
| B | P-B2 | 4k still > 24k by > 5 pp at 4,800 steps | met (+15.3 pp, all seeds) | scale_grid_budget/prereg_verdicts.md |
| X (width under V4k) | P-X1 | d256/V4k within 3 pp of d384/V4k; d224→d256 adopted rise | rejected on both parts (−10.6 pp, 5/5) | scale_grid_width_v4k/prereg_verdicts.md |
| X | P-X2 | SD at d256 ≤ 2× SD at d384 | rejected (4.4 vs 1.6) | scale_grid_width_v4k/prereg_verdicts.md |
| A (attribute-count control) | P-A1 | at A = 2 the shallowest depth within 3 pp of L = 8 is L = 2 | rejected as written (D2 → D4 +6.3 pp adopted); note: P-A1 mis-operationalised L = A + 1, which predicts L = 3, so this alone does not reject the heuristic | scale_grid_depth_a2/prereg_verdicts.md |
| A | P-A2 | D2 → D4 rise at A = 2 of similar size to A = 3 and adopted | descriptively consistent (+6.3 vs +6.5 pp; difference −0.2 pp, 90 % CI [−5.7, +5.3]); shape above L = 4 not identical | scale_grid_depth_a2/prereg_verdicts.md |
| A-L3 (direct test of L = A + 1) | P-L3-1 | at A = 2, L = 3 reaches the L = 4 level (D2→D3 adopted, D3→D4 not); at A = 3 D3→D4 adopted; interaction CI excludes 0 | not supported by the rule at five seeds (A = 2: D2→D3 +8.8 pp, 4/5 seeds, not adopted; D3→D4 +3.9 pp, 4/5; interaction (D3−D2) −7.9 pp, 90 % CI [−20.9, +5.1]); data compatible with no shift and with a modest shift; not a rejection of a general relation | scale_grid_depth_l3/prereg_verdicts.md |
| A-L3 | P-L3-2 | D3 occupies the same position relative to D2/D4 in both policies; interaction CI includes 0 | inconclusive: the relative position of L = 3 differed descriptively (A = 3: at the L = 2 level; A = 2: intermediate) but the between-policy difference is statistically inconclusive ((D3−D2) −7.9 pp, 90 % CI [−20.9, +5.1]; (D4−D3) −0.4 pp, CI [−7.7, +6.8]) | scale_grid_depth_l3/prereg_verdicts.md |
| A-L3 | P-L3-3 | D3 → D4 not adopted in either policy (L = 3 already sufficient) | sufficiency of L = 3 not established (adoption rule met only because one seed dissents in each policy; D4−D3 +3.4 / +3.9 pp, CIs include 0, TOST ±3 pp fails) | scale_grid_depth_l3/prereg_verdicts.md |

Source: `config/*_series.json; backend/reports/*/prereg_verdicts.md`
