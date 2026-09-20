# Unseen-frame hold-out (2,000 rows, 32 frames in 6 families) — analysis

Runs: C4kL4x5, D4_V24kx5, X320_V4kx5, deployed_W384_L8_V24kx5, selected_V4k_L8x5; quantized selected x5.
Development-test values are read from tables/T08 and T10 (frozen), not restated here by hand.

| configuration | params | seeds | hold-out exact % (mean ± SD) | hierarchical bootstrap 90 % CI | dev test exact % | drop (pp) | coarse % | strict % | valid output % |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| selected: d 384, L 8, 4k natural tokenizer | 15.7 M | 5 | 58.7 ± 1.7 | [55.9, 61.4] | 86.5 ± 1.8 | −27.8 | 70.6 | 44.7 | 100.0 |
  - attribute errors, % of wrong rows: colour 12.7, emotion 65.0, intensity 30.1, not a policy tuple 9.2
  - family-resampled 90 % CI [56.0, 66.6]; unweighted mean over the six families 60.6 %
  - by frame family: color_only 74.6, emotion_only_intensity 58.8, emotion_only_neutral 55.7, fallback_intensity 79.4, fallback_neutral 40.0, mixed 55.0
| deployed architecture: d 384, L 8, 24k production tokenizer | 23.4 M | 5 | 57.4 ± 2.4 | [54.4, 60.2] | 80.8 ± 3.6 | −23.4 | 70.5 | 45.3 | 100.0 |
  - attribute errors, % of wrong rows: colour 10.5, emotion 73.7, intensity 31.0, not a policy tuple 2.9
  - family-resampled 90 % CI [54.8, 67.7]; unweighted mean over the six families 62.5 %
  - by frame family: color_only 75.2, emotion_only_intensity 69.0, emotion_only_neutral 49.4, fallback_intensity 76.7, fallback_neutral 52.7, mixed 52.2
| d 320, L 8, 4k natural tokenizer | 11.2 M | 5 | 58.1 ± 1.9 | [54.9, 61.0] | 83.8 ± 3.4 | −25.7 | 70.5 | 44.9 | 100.0 |
  - attribute errors, % of wrong rows: colour 10.3, emotion 64.0, intensity 31.9, not a policy tuple 11.7
  - family-resampled 90 % CI [55.5, 66.3]; unweighted mean over the six families 63.8 %
  - by frame family: color_only 71.6, emotion_only_intensity 62.8, emotion_only_neutral 52.8, fallback_intensity 74.2, fallback_neutral 67.3, mixed 54.5
| d 384, L 4, 4k natural tokenizer | 8.6 M | 5 | 55.0 ± 4.0 | [51.5, 58.6] | 82.0 ± 6.4 | −27.0 | 67.6 | 42.9 | 100.0 |
  - attribute errors, % of wrong rows: colour 12.9, emotion 67.1, intensity 29.5, not a policy tuple 8.6
  - family-resampled 90 % CI [51.8, 63.1]; unweighted mean over the six families 60.1 %
  - by frame family: color_only 65.7, emotion_only_intensity 53.7, emotion_only_neutral 51.5, fallback_intensity 81.4, fallback_neutral 56.4, mixed 52.1
| d 384, L 4, 24k production tokenizer | 16.3 M | 5 | 52.1 ± 3.8 | [48.4, 55.7] | 81.7 ± 4.9 | −29.6 | 65.6 | 42.7 | 100.0 |
  - attribute errors, % of wrong rows: colour 18.2, emotion 69.5, intensity 32.7, not a policy tuple 3.7
  - family-resampled 90 % CI [48.7, 60.1]; unweighted mean over the six families 51.7 %
  - by frame family: color_only 59.8, emotion_only_intensity 66.6, emotion_only_neutral 48.5, fallback_intensity 62.8, fallback_neutral 23.6, mixed 48.7
| selected, mixed 4/6/8-bit export (17.1 MB) | 15.7 M | 5 | 58.4 ± 1.7 | [55.5, 61.1] | 86.3 ± 1.9 | −27.9 | | | |
  - quantized − fp32, paired by seed: -0.60, +0.25, -0.05, -0.95, -0.15 pp; mean -0.30, 90 % CI [-0.75, +0.15]

## Selected vs deployed architecture on the hold-out

Paired by seed ([42, 43, 44, 45, 46]): +4.8, -0.2, +3.5, -1.3, -0.5 pp; mean +1.2, 90 % t CI [-1.3, +3.8]; seeds favouring the selected model 2/5.
Superiority (difference > 0): p = 0.181. Equivalence TOST ±3 pp: equivalence within ±3 pp NOT established (p = 0.109).
Exploratory non-inferiority at a −3 pp margin: p = 0.012; the 90 % CI lower bound is -1.3 pp, so the selected model is not materially worse than the deployed architecture at this margin. The margin was not prespecified for this comparison.
Row-level discordant pairs pooled over seeds: selected-only correct 1282, deployed-only correct 1158.

## Frame-level spread (selected model, mean over 5 seeds)

32 frames recovered; unmatched rows 0. Worst frame mixed#2 24.1 %, best fallback_intensity#3 91.9 %, spread 67.8 pp.

| frame family | frame | exact % (5-seed mean) |
|---|---|--:|
| mixed | mixed#2 | 24.1 |
| emotion_only_intensity | emotion_only_intensity#1 | 26.1 |
| emotion_only_neutral | emotion_only_neutral#2 | 32.0 |
| fallback_neutral | fallback_neutral#1 | 33.3 |
| mixed | mixed#5 | 34.7 |
| fallback_neutral | fallback_neutral#2 | 36.0 |
| emotion_only_neutral | emotion_only_neutral#1 | 38.2 |
| color_only | color_only#3 | 45.0 |
| emotion_only_intensity | emotion_only_intensity#4 | 52.7 |
| fallback_neutral | fallback_neutral#3 | 53.3 |
| mixed | mixed#3 | 54.0 |
| mixed | mixed#8 | 54.5 |
| mixed | mixed#11 | 54.5 |
| mixed | mixed#1 | 58.7 |
| mixed | mixed#6 | 59.6 |
| fallback_intensity | fallback_intensity#2 | 62.0 |
| mixed | mixed#9 | 62.1 |
| mixed | mixed#12 | 62.2 |
| mixed | mixed#10 | 63.0 |
| emotion_only_neutral | emotion_only_neutral#4 | 64.3 |
| mixed | mixed#4 | 65.1 |
| mixed | mixed#7 | 69.6 |
| color_only | color_only#6 | 73.3 |
| color_only | color_only#5 | 74.1 |
| emotion_only_intensity | emotion_only_intensity#3 | 78.5 |
| fallback_intensity | fallback_intensity#1 | 80.0 |
| emotion_only_neutral | emotion_only_neutral#3 | 81.7 |
| color_only | color_only#2 | 83.4 |
| emotion_only_intensity | emotion_only_intensity#2 | 87.0 |
| color_only | color_only#4 | 88.4 |
| color_only | color_only#1 | 88.8 |
| fallback_intensity | fallback_intensity#3 | 91.9 |
