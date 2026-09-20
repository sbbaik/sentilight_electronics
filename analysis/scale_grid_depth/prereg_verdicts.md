# Depth series (D) — preregistered predictions and verdicts

- Config frozen: `config/depth_series.json` (sha256 a5afa501…, recorded in `depth_series.inputs.sha256` at launch 2026-09-05 10:24)
- Runs: L ∈ {2, 4, 6, 8, 12, 16} × seeds 42/43/44, d = 384, d_ff = 1024, 6 heads, V = 24k, pretrain 2,400 steps on clean corpus (per depth), SFT 4 epochs on K240 policy-only + coverage-fill, eval on K240 `test_rule.jsonl` (2,000 rows)
- Finished 2026-09-05 12:12 (1 h 48 min); 0 failed tasks. Analysis: `width_analysis.md/json` (sorted by L), `scale_grid_summary.md/json`

## Results (mean ± SD over seeds)

| L | Params | Layers / attribute (A = 3) | Strict % | Coarse % | Exact tuple % | Latency ms |
|--:|--:|--:|--:|--:|--:|--:|
| 2 | 12.76M | 0.67 | 46.67 ± 1.19 | 83.78 ± 1.46 | 77.40 ± 1.91 | 67 |
| 4 | 16.30M | 1.33 | 49.47 ± 0.55 | 87.65 ± 0.67 | 83.92 ± 1.51 | 117 |
| 6 | 19.84M | 2.00 | 48.55 ± 1.19 | 84.68 ± 3.07 | 80.35 ± 3.68 | 163 |
| 8 | 23.38M | 2.67 | 49.33 ± 0.19 | 84.93 ± 0.55 | 79.08 ± 1.34 | 216 |
| 12 | 30.46M | 4.00 | 48.35 ± 1.05 | 84.77 ± 1.76 | 79.42 ± 1.16 | 314 |
| 16 | 37.54M | 5.33 | 46.93 ± 3.04 | 81.03 ± 6.33 | 73.15 ± 7.85 | 420 |

Adopted adjacent steps (Holm p < 0.05, all seeds same sign): D2→D4 on all three metrics (exact +6.52 pp), and D4→D6 as a *drop* on coarse (−2.97). Nothing above D4 is adopted as a gain. D12→D16 exact −6.27 pp is significant but seed-split (s42 63.8, s43 83.0, s44 72.7).

## Verdicts

| Prediction | As written | Verdict |
|---|---|---|
| P-D1 | Exact rises D2→D4 and D4→D6 (both adopted); ≥ A = 3 layers needed before flattening | **Half met.** D2→D4 adopted (+6.5 pp exact). D4→D6 is not a rise but a small drop (coarse drop adopted). The curve peaks at L = 4 ≈ A + 1, earlier than the "one to two layers per attribute" band (6–12) the paper used. |
| P-D2 | No adopted positive gain above D8 | **Met.** D8→D12 and D12→D16 show no adopted gain; D16 is worse and unstable. |
| P-D3 | D8 reproduces W384 within 3 pp | **Met exactly.** Identical means and SDs (49.33 / 84.93 / 79.08): the pretrain → SFT → eval pipeline is bit-reproducible for a given seed, so seed spread is the only noise source in this study. |

## Observations to carry into the paper

1. **Depth is nearly irrelevant to accuracy above L = 4.** Two layers already reach 77% exact; four layers are best (84%); 6–12 layers sit at 79–80% within seed noise; 16 layers degrade and become seed-unstable at fixed compute (2,400 pretrain steps is too little for the deepest model).
2. **Depth is the latency lever.** Wall-clock grows linearly with L (67 → 420 ms for the 96-step reference decoder, 26 ms per layer) while width barely changed latency (209–219 ms across d = 128–512 at L = 8). For edge deployment the recipe should therefore prefer *shallow and wide*: pick L ≈ A + 1 and buy accuracy with d.
3. **Reframe the depth heuristic.** Replace "one to two layers per attribute" with "about one layer per attribute plus one": L* ≈ A + 1 = 4 here. The paper's L = 8 was twice what the task needed; at equal accuracy L = 4 halves inference time.
4. **The deployed 23M model (d = 384, L = 8) is not on the Pareto front** of this grid: D4 (16.3M) is more accurate and 1.8× faster. This is a concrete, quotable outcome of the sizing exercise.
5. Embedding share at L = 2 is 72%; with d fixed, shallow models are almost all vocabulary. This strengthens the case for a vocabulary series (V) as the remaining lever.

## Caveats

- Single width (d = 384) and single K_eff (240); the depth–width interaction is not measured.
- Step-matched by step count; D16's degradation may be under-training rather than a capacity effect.
- Latency is from the KV-cache-free 96-step reference decoder (IoTJ Tier 1 protocol); the per-layer cost, not the absolute value, is the transferable quantity.
