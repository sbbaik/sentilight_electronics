# Generative decoding vs a 240-class head on the same backbone

Same pretrained checkpoints, same fine-tuning rows, same five seeds, same evaluation rows. The generative model has
15,698,304 parameters and the classifier 15,790,704; they differ in the output formulation and nothing else.

## frame hold-out

- generative 58.7 ± 1.7 %, head 58.3 ± 2.3 % (5 seeds each)
- per-seed difference (head − generative): -3.30, +2.60, -4.85, +1.25, +2.25 pp
- mean -0.41 pp, 90 % t CI [-3.68, +2.86], seed → row bootstrap 90 % CI [-3.01, +1.95]
- row-level McNemar combined over seeds: Stouffer z = -0.69, p = 0.491; the head is higher in 3/5 seeds
- **inconclusive: the interval includes zero**
- coarse three-bin (recomputed with the same scorer): generative 70.6 %, head 69.1 %
- attribute accuracy, generative vs head: colour 90.9 vs 92.3, emotion 69.3 vs 86.7, intensity 83.7 vs 68.8
- valid output: generative 100.0 %, head 100 % by construction (a 240-class head cannot emit an out-of-schema answer)

## paraphrase hold-out

- generative 7.9 ± 0.6 %, head 10.3 ± 0.6 % (5 seeds each)
- per-seed difference (head − generative): +2.40, +3.50, +3.45, +1.25, +1.70 pp
- mean +2.46 pp, 90 % t CI [+1.49, +3.43], seed → row bootstrap 90 % CI [+1.61, +3.31]
- row-level McNemar combined over seeds: Stouffer z = +7.14, p = 0.000; the head is higher in 5/5 seeds
- **the head is higher and the interval excludes zero**
- coarse three-bin (recomputed with the same scorer): generative 22.0 %, head 23.8 %
- attribute accuracy, generative vs head: colour 38.6 vs 44.4, emotion 31.1 vs 46.8, intensity 48.0 vs 45.9
- valid output: generative 100.0 %, head 100 % by construction (a 240-class head cannot emit an out-of-schema answer)

