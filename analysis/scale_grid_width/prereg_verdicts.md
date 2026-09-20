# Width series (W) — preregistered predictions and verdicts

- Config frozen: `config/width_series.json` (sha256 a9d0f88c…, recorded in `width_series.inputs.sha256` at launch 2026-09-04 21:05)
- Runs: 7 widths × 3 seeds, L = 8, V = 24k, pretrain 2,400 steps on clean corpus, SFT 4 epochs on K240 policy-only + coverage-fill (49,093 rows), eval on K240 `test_rule.jsonl` (2,000 rows, all 240 tuples covered, no conflicting-gold inputs)
- Finished 2026-09-04 23:01; 0 failed tasks. Analysis: `width_analysis.md/json`, `scale_grid_summary.md/json`

## Results (mean ± SD over seeds 42/43/44)

| Scale | d | Params | Strict % | Coarse % | Exact tuple % |
|---|--:|--:|--:|--:|--:|
| W128 | 128 | 4.68M | 43.22 ± 1.67 | 73.20 ± 1.23 | 52.68 ± 2.27 |
| W192 | 192 | 8.15M | 46.90 ± 2.06 | 82.30 ± 1.99 | 73.63 ± 2.82 |
| W224 | 224 | 10.25M | 44.40 ± 2.23 | 77.23 ± 5.61 | 68.68 ± 6.55 |
| W256 | 256 | 12.37M | 48.15 ± 1.14 | 85.48 ± 2.04 | 79.73 ± 3.57 |
| W320 | 320 | 17.60M | 48.82 ± 0.71 | 87.20 ± 0.99 | 81.93 ± 1.54 |
| W384 | 384 | 23.38M | 49.33 ± 0.19 | 84.93 ± 0.55 | 79.08 ± 1.34 |
| W512 | 512 | 37.59M | 50.88 ± 2.30 | 88.62 ± 3.56 | 83.70 ± 4.81 |

Adopted adjacent steps (Holm p < 0.05 and all three seeds same sign): W128→W192 (coarse +9.10, exact +20.95), W224→W256 (strict +3.75, coarse +8.25, exact +11.05), W320→W384 (coarse −2.27, exact −2.85). Every other step fails the seed-sign rule.

## Verdicts

| Prediction | As written | Verdict |
|---|---|---|
| P-W1 | Coarse rises steeply W128→W256; the largest single step is W224→W256 | **Partly met.** Rise W128→W256 is +12.3 pp coarse / +27.1 pp exact. The largest adopted step is W128→W192 (+9.10 coarse), with W224→W256 second (+8.25). W192→W224 is a *drop* (−5.07 coarse; seeds split: s43 +1.3, s42 −5.7, s44 −10.7). The knee lies in the 192–256 band, which contains K_eff = 240, but the data do not localise it to the single step named in the prediction. |
| P-W2 | Above W256 every step gains less than W224→W256 | **Met.** W256→W320 +1.72, W320→W384 −2.27, W384→W512 +3.68 (coarse); none is positive-adopted. Exact tuple: +2.20, −2.85, +4.62. |
| P-W3 | W384 ≥ IoTJ Gen-Policy 23M (49.3 / 78.8) | **Met** (49.33 / 84.93), noting the test set differs (2,000 rows, conflicting-gold rows removed). Plausibility check only. |

## Observations to carry into the paper

1. The width curve is a shoulder, not a cliff: d = 128 (below K_eff) already reaches 73% coarse / 53% exact. The heuristic d ≳ K_eff marks where returns flatten (≈ 256), not a threshold below which the task fails. Reframe eq. (9) accordingly.
2. Above d ≈ 256 the curve is flat within seed noise (85–89% coarse); W512 gains come from two of three seeds (s43 is 83.6%). Strict is nearly flat from W192 onward (46.9 → 50.9), i.e. strict is metric-limited (emotion-constraint clauses), not capacity-limited.
3. W224 is the anomaly: highest seed SD (5.6 coarse) and a mean below W192. It is the only config with head_dim 56 (4 heads); the other six use head_dim 64. Treat as a possible head-geometry effect and, if space allows, rerun W224 with 7 heads of 32 or drop it from the fitted curve with disclosure.
4. Exact tuple match is the most informative metric for this test set (largest dynamic range, 52.7 → 83.7); coarse saturates near 88% and strict near 50%.
5. Latency is flat (209–219 ms) because the reference decoder runs 96 steps without KV cache; width does not change wall-clock at this scale.
