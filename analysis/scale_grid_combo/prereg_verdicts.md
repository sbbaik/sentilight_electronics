# Combined cell C4kL4 (d = 384, L = 4, V = 4k natural) — verdicts

- Launched 2026-09-05 17:38, finished 17:49 (11 min for 3 seeds incl. pretraining); 0 failures. Inputs frozen in `combo.inputs.sha256`.
- Same pretrain budget (2,400 steps), SFT (K240 policy-only + fill, 4 epochs) and test set (2,000 rows) as every other series.

## The depth × vocabulary factorial (exact tuple match %, mean ± SD over seeds 42/43/44)

| | V = 24k production tokenizer | V = 4k natural tokenizer |
|---|---:|---:|
| L = 8 | 79.1 ± 1.3 (W384, 23.4M, 225 ms) | 86.8 ± 1.4 (V2 V4k, 15.7M, 202 ms) |
| L = 4 | 83.9 ± 1.5 (D4, 16.3M, 122 ms) | **85.7 ± 4.4 (C4kL4, 8.6M, 108 ms)** |

Per-seed C4kL4 exact: 79.4 / 88.8 / 88.9 (seed 42 is the low one; strict 50.7 ± 1.5, coarse 89.5 ± 3.6).

Row-level McNemar (Stouffer, Holm over 9 tests, sign rule):

| Contrast | Exact Δ pp | Per-seed | Verdict |
|---|--:|---|---|
| V2 V4k (L8) → C4kL4 | −1.15 | −5.8 / +2.1 / +0.3 | no difference (Holm p 0.36) |
| D4 (24k, L4) → C4kL4 | +1.75 | −5.3 / +3.5 / +7.1 | significant but seed-split, not adopted |
| W384 (deployed config) → C4kL4 | **+6.58** | +1.7 / +7.8 / +10.2 | **adopted** (coarse +4.5 significant but seed-split) |

## Verdicts

| Prediction | Verdict |
|---|---|
| P-C1: C4kL4 within 3 pp of V2 V4k | **Met** (−1.15 pp; no adopted difference). Halving depth costs nothing at V = 4k, as it cost nothing at V = 24k. |
| P-C2: latency ≈ half of the L8 model | **Met.** 108 ms vs 202 ms (reference 96-step decoder); D4 122 ms, W384 225 ms. |
| P-C3: additive factors (vocab effect at L4 within 3 pp of vocab effect at L8, +7.7) | **Rejected.** Vocab effect at L4 is +1.75 pp (vs +7.7 at L8): the two changes are sub-additive. Each alone lifts the deployed configuration by 5–8 pp; together they reach about the same ceiling (85.7–86.8), not the sum. |

## Reading

1. **The deployed configuration (d 384, L 8, V 24k, 23.4M) is dominated in every direction.** Halving depth (D4) or shrinking vocabulary (V2 V4k) each beats it; doing both gives an 8.6M model that is 6.6 pp more exact (adopted, all seeds) at 48 % of the latency and 37 % of the parameters.
2. **Sub-additivity suggests a shared ceiling near 86–89 % exact** on this test set at this pretraining budget, reached once the model stops wasting capacity on either an under-trained embedding table or superfluous depth. The remaining errors appear to arise primarily from input-side generalisation rather than insufficient pretraining optimisation; SFT-data limits, label ambiguity and decoding errors are not excluded (see `error_decomposition.md`).
3. **Seed spread widens at the smallest model** (SD 4.4 vs 1.4 for V2 V4k), consistent with the pattern seen at every knee in this study: configurations at the edge of sufficiency train less reliably. For deployment, L = 4 with V = 4k should be trained with seed selection or a slightly larger d.
4. Recipe consequence: the co-designed point (L = A + 1, V by token exposure, d from the K_eff shoulder) is 8.6M parameters for K_eff = 240 — about 40 % of what eq. (8) with the paper's original assumptions produced (23.4M), and at the bottom of the 10⁷ band it predicted.

## Caveats

- One combined cell; interactions with d and with K_eff are untested.
- Seed 42 of C4kL4 is 9 pp below its siblings; with three seeds this single run drives the SD. A five-seed replicate of C4kL4 would settle whether the small model is genuinely less stable.
- All latencies are from the KV-cache-free reference decoder; ratios, not absolute values, transfer.
