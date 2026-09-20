# Attribute-count control (A = 2) for the depth heuristic — verdicts

- Policy A2K192: colour (15) × emotion (11), intensity fixed at neutral → A = 2 attributes, K_eff = (15+1)(11+1)×1 = 192 (0 collisions). Same d = 384, 24k production tokenizer, pretrain checkpoints, seeds 42–44 and SFT budget as the A = 3 depth series (K_eff = 240). 12 runs (SFT + eval), 0 failures; inputs frozen in `inputs.sha256`.
- Question: does the shallowest depth without consistent loss move from L = 4 (A = 3) to L ≈ 3 or 2 when the policy reads only two attributes (heuristic L = A + 1)?

## Results (exact tuple match %, mean ± SD, three seeds)

| L | A = 2 (K_eff 192) | A = 3 (K_eff 240, seeds 42–44) |
|--:|--:|--:|
| 2 | 78.9 ± 3.8 | 77.4 ± 1.9 |
| 4 | 85.2 ± 5.7 | 83.9 ± 1.5 |
| 6 | 83.1 ± 3.3 | 80.4 ± 3.7 |
| 8 | 86.5 ± 2.1 | 79.1 ± 1.3 |

Adjacent steps at A = 2 (row-level McNemar, Stouffer, Holm, sign rule): D2 → D4 **+6.3 pp exact, adopted (all seeds)**; D4 → D6 −2.1, not adopted; D6 → D8 seed-split. At A = 3 the same pattern held: D2 → D4 +6.5 pp adopted, nothing above D4 adopted.

## Verdicts

| Prediction | Verdict |
|---|---|
| P-A1 (depth tracks attributes): at A = 2 the shallowest depth within 3 pp of L = 8 is L = 2 | **Rejected.** D2 is 7.6 pp below D8 at A = 2 and D2 → D4 is an adopted +6.3 pp rise, exactly as at A = 3. |
| P-A2 (depth independent of A in this range): D2 → D4 rise of similar size, adopted | **Supported.** +6.3 pp (A = 2) vs +6.5 pp (A = 3); the no-loss depth is L = 4 in both. |

## Reading
- Removing one attribute did not move the depth curve. The first two layers to four layers step matters regardless of whether the policy composes two or three attributes; above L = 4 gains are within seed noise in both series.
- **L = A + 1 is not supported as a rule.** L = 4 should be reported as an empirical no-loss depth for this task family (both policies), and depth should be chosen by latency once L ≥ 4. The recipe's depth step becomes: "sweep L from 2 upward; take the shallowest depth with no consistent loss; expect it to be small and largely independent of the attribute count in this range."
- Absolute levels across the two series are not comparable (different policies, test sets and K_eff); only the shape of the depth curve is.

## Caveats
- Two attribute counts (2, 3), one width, one budget, three seeds. A = 4 was not tested; the conclusion is "no evidence for attribute-linked depth", not proof of independence.
