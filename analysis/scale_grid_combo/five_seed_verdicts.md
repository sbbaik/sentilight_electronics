# Five-seed re-adjudication of the depth × vocabulary factorial, W224, and quantization (2026-09-05)

Seeds 45 and 46 were added to C4kL4, to the three reference cells (W384, D4, V2 V4k) and to W192 / W224 / W256.
Original three-seed results are kept in the per-series verdict files; nothing was replaced.

## Depth × vocabulary factorial at five seeds (exact tuple match %, mean ± SD; per-seed in brackets)

| | V = 24k production tokenizer | V = 4k natural tokenizer |
|---|---|---|
| L = 8 | 80.8 ± 3.2 (W384, 23.4M) [77.7, 80.9, 78.6, **86.9**, 79.7] | **86.5 ± 1.6** (V2 V4k, 15.7M) [85.2, 86.7, 88.6, 84.3, 87.9] |
| L = 4 | 81.7 ± 4.4 (D4, 16.3M) [84.8, 85.2, 81.8, **73.2**, 83.4] | 82.0 ± 5.7 (C4kL4, 8.6M) [79.4, 88.7, 88.9, **77.2**, **75.6**] |

Row-level McNemar over five seeds (Stouffer, Holm over 24 tests, all-seeds sign rule):

| Contrast | exact Δ pp | seeds agreeing | Holm p | verdict |
|---|--:|--:|--:|---|
| W384 → V2 V4k | **+5.79** | 4 / 5 (seed 45: −2.5) | < 1e-16 | significant; not adopted under the all-seeds rule |
| W384 → D4 | +0.92 | 4 / 5 (seed 45: −13.6) | 1e-4 | not adopted; mean within noise |
| W384 → C4kL4 | +1.22 | 3 / 5 | 0.06 | no difference |
| V2 V4k → C4kL4 | −4.57 | 4 / 5 | 1e-13 | C4kL4 worse than V2 V4k in 4 of 5 seeds |
| D4 → C4kL4 | +0.30 | 3 / 5 | 0.50 | no difference |

### What changed from the three-seed reading
- **The "8.6M beats 23.4M by 6.6 pp" claim does not survive.** At five seeds C4kL4 equals the deployed configuration on average (+1.2 pp, p = 0.06) with the largest spread of any cell (SD 5.7; two of five seeds below 78 %).
- **The vocabulary effect survives; the depth effect does not.** V2 V4k is 5.8 pp above the deployed configuration with the *lowest* variance in the table (SD 1.6). D4's three-seed advantage (+4.8) collapsed to +0.9 when seed 45 trained to 73.2 %.
- The single anomalous seed on each side (W384 seed 45 at 86.9 %, D4 seed 45 at 73.2 %) is why the all-seeds sign rule rejects even the vocabulary contrast; the rule is doing what it was designed to do. Report both the rule verdict and the 4/5 agreement.

### Recommendation for the paper's final model
- **Selected deployment model: V2 V4k — d 384, L 8, V 4k natural, 15.7M**, 86.5 ± 1.6 % exact / 90.4 % coarse, 203 ms reference latency. Statistical result: +5.8 pp over the deployed configuration on average, but the preregistered all-seeds direction rule is not met (4/5). Engineering choice: highest mean, smallest seed variance and 67 % of the deployed parameters among all tested cells. The selection is justified by accuracy, stability and size together, not by a confirmed hypothesis. Seed-level CIs and a hierarchical bootstrap are in `seed_level_stats.md`.
- **C4kL4 — 8.6M** (82.0 ± 5.7 %, 107 ms) is the smallest configuration but is sensitive to the training seed (two of five replicates below 78 %), so it is **not selected as the default deployment model**. It is reported with its five-seed mean and range only. If a single representative checkpoint were ever needed it must be chosen on the validation split, never on the test set.
- Depth halving is therefore "free in the mean, not free in the variance" — this replaces the three-seed statement that L = 4 costs nothing.

## Width series with five seeds at 192 / 224 / 256

| d | n | exact % | coarse % |
|--:|--:|--:|--:|
| 192 | 5 | 70.6 ± 4.8 | 80.0 ± 3.6 |
| 224 | 5 | 70.6 ± 6.0 | 78.5 ± 4.8 |
| 256 | 5 | 78.0 ± 3.5 | 84.3 ± 2.5 |

W192 → W224: +0.05 pp exact, not significant. W224 → W256: +7.4 pp exact, coarse (+5.9) and strict (+2.5) **adopted** with all five seeds agreeing. The three-seed "W224 dip" was seed noise: at five seeds 192 and 224 are identical and the knee is the 224 → 256 step, i.e. exactly at the d ≈ K_eff = 240 crossing that P-W1 predicted. P-W1 is now **met** (largest adopted step at 224 → 256; 128 → 192 remains large but was measured at three seeds). W224's head_dim = 56 is not evidence of a head-geometry effect. Both readings are reported; neither is deleted.

## Quantization of C4kL4 (five seeds, mixed 4/6/8-bit, group 64, embedding fp32)

| metric | mean Δ (q − fp32) pp | 90 % CI (seed t) | TOST ±3 pp |
|---|--:|---|---|
| exact | −0.42 | [−1.20, +0.36] | pass |
| coarse | −0.28 | [−0.76, +0.20] | pass |
| strict | −0.14 | [−0.46, +0.18] | pass |

Seed 42 alone shows a significant −1.6 pp exact drop; the other four are within noise. File size 12.3 MB (fp32 weights 34.5 MB; the fp32 embedding is 6.1 MB of the 12.3). The quantized evaluator dequantizes at load and decodes with a KV cache (≈58 ms), so its latency is not a quantization speed-up measurement.

## Final table (five seeds; latency = KV-cache-free 96-step reference decoder)

| Configuration | params | fp32 weights | exact % | coarse % | invalid JSON | latency mean / p95 | speed vs deployed |
|---|--:|--:|--:|--:|--:|--:|--:|
| W384 deployed cfg | 23.4M | 93.5 MB | 80.8 ± 3.2 | 85.8 ± 2.4 | 0.00 % | 216 / 234 ms | 1.00× |
| D4 | 16.3M | 65.2 MB | 81.7 ± 4.4 | 86.1 ± 2.9 | 0.00 % | 118 / 127 ms | 1.83× |
| **V2 V4k** | 15.7M | 62.8 MB | **86.5 ± 1.6** | **90.4 ± 1.0** | 0.00 % | 203 / 225 ms | 1.07× |
| C4kL4 | 8.6M | 34.5 MB | 82.0 ± 5.7 | 86.8 ± 4.3 | 0.01 % | 107 / 114 ms | 2.03× |
| C4kL4 mixed-bit | 8.6M | 12.3 MB file | 81.5 ± 5.5 | 86.5 ± 4.2 | 0.01 % | (58 ms, KV cache) | — |

## Caveats
- W128, W320, W512 and every K-series / D-series cell other than D4 remain at three seeds.
- Seed sensitivity is itself a finding: the two configurations that changed verdict (D4, C4kL4) are the shallow ones. Shallow models at this budget should be reported with ≥ 5 seeds.
- The all-seeds sign rule with five seeds is stricter than with three; contrasts at 4/5 agreement and p < 1e-10 are reported as "significant, not adopted" rather than hidden.

## Reporting rule for the paper
Only five-seed results are presented in the paper; three-seed interim readings (including the W224 dip) stay in these repository reports as process records.

## Addendum (2026-09-06): final-model quantization and deployment benchmark
- V2 V4k mixed-4/6/8-bit, five seeds: exact −0.19 pp [−0.52, +0.14], coarse −0.07, strict −0.11; TOST ±3 pp passes on all three; 0 invalid JSON (`../scale_grid_vocab_natural_q4/quant_equivalence.md`). File 17.1 MB vs 47.8 MB for the 24k-vocabulary mixed-bit export (fp32 embedding dominates the latter).
- Seed-level statistics for W384 → V2 V4k: 90 % t-CI [+1.1, +10.5], 95 % t-CI [−0.3, +11.9], hierarchical bootstrap 95 % [+1.4, +9.1], DL random effects [+1.3, +10.2] (`seed_level_stats.md`).
- CPU deployment benchmark through the production runtime, 4 threads: V2 V4k mixed-bit median 95 ms / p95 105 ms, peak RSS 665 MB, load 0.10 s; deployed-config mixed-bit 101 / 108 ms, 729 MB; C4kL4 mixed-bit 52 / 70 ms (`../deploy_benchmark_t4/summary.md`). End-to-end bulb measurements require the lab network (`tools/e2e_latency_probe.py`).
