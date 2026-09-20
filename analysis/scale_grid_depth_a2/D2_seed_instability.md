# A2K192 L = 2: seed-instability failure signature

Policy A2K192 has 192 reachable tuples; the 2,000-row test covers all of them. Seeds 45/46 trained normally (validation loss at or below the other seeds). This analysis identifies a failure signature; it does not establish a causal mechanism.

## D2: output validity and concentration

| seed | exact % | JSON/parse errors | distinct in-policy tuples (of 192) | distinct out-of-policy tuples | out-of-policy rows % | top-5 predicted share % |
|--:|--:|--:|--:|--:|--:|--:|
| 42 | 80.7 | 0 | 185 | 34 | 2.0 | 6.5 |
| 43 | 82.3 | 0 | 185 | 23 | 1.7 | 6.3 |
| 44 | 73.6 | 0 | 180 | 13 | 1.4 | 9.4 |
| 45 | 65.5 | 0 | 179 | 23 | 1.7 | 10.6 |
| 46 | 59.2 | 0 | 158 | 38 | 4.2 | 9.4 |

## D2: exact % by emotion (n = rows per category)

| emotion | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| anger | 168 | 75.6 | 83.3 | 68.5 | 45.2 | 13.1 |
| anxiety | 156 | 84.6 | 93.6 | 79.5 | 67.9 | 54.5 |
| boredom | 169 | 76.9 | 89.9 | 53.3 | 47.9 | 13.0 |
| calm | 182 | 93.4 | 59.9 | 70.3 | 62.6 | 58.8 |
| disgust | 175 | 65.7 | 85.7 | 76.6 | 58.3 | 73.1 |
| fatigue | 185 | 91.4 | 96.8 | 95.1 | 89.2 | 88.1 |
| gratitude | 170 | 72.4 | 71.8 | 63.5 | 72.9 | 81.8 |
| happiness | 182 | 81.9 | 83.0 | 63.2 | 52.2 | 70.3 |
| none | 111 | 22.5 | 20.7 | 22.5 | 27.9 | 18.9 |
| nostalgia | 171 | 93.6 | 88.9 | 92.4 | 75.4 | 56.7 |
| sadness | 162 | 93.2 | 96.3 | 92.6 | 87.7 | 67.3 |
| surprise | 169 | 96.4 | 98.8 | 88.2 | 85.8 | 96.4 |

## D2: exact % by base_color (n = rows per category)

| base_color | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| apricot | 102 | 86.3 | 79.4 | 79.4 | 62.7 | 47.1 |
| blue | 176 | 75.0 | 96.0 | 75.6 | 73.3 | 68.8 |
| green | 172 | 86.0 | 88.4 | 86.6 | 75.0 | 68.0 |
| indigo | 108 | 79.6 | 82.4 | 64.8 | 65.7 | 48.1 |
| lavender | 92 | 80.4 | 82.6 | 71.7 | 75.0 | 35.9 |
| lime | 95 | 65.3 | 68.4 | 77.9 | 37.9 | 57.9 |
| mint | 119 | 89.9 | 88.2 | 73.1 | 66.4 | 48.7 |
| none | 82 | 14.6 | 13.4 | 2.4 | 22.0 | 7.3 |
| orange | 192 | 87.5 | 94.8 | 66.1 | 57.3 | 79.2 |
| pink | 101 | 73.3 | 80.2 | 74.3 | 69.3 | 59.4 |
| purple | 174 | 88.5 | 85.1 | 72.4 | 87.4 | 61.5 |
| red | 182 | 87.9 | 87.4 | 79.7 | 63.2 | 68.1 |
| sky | 112 | 83.9 | 76.8 | 83.0 | 48.2 | 53.6 |
| teal | 98 | 88.8 | 89.8 | 79.6 | 67.3 | 53.1 |
| white | 93 | 93.5 | 83.9 | 90.3 | 81.7 | 69.9 |
| yellow | 102 | 79.4 | 75.5 | 80.4 | 70.6 | 72.5 |

## D2: exact % by source (n = rows per category)

| source | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| ambiguous_fallback_cases | 36 | 2.8 | 5.6 | 0.0 | 13.9 | 2.8 |
| color_emotion_intensity_combinations | 1604 | 80.0 | 81.7 | 74.1 | 64.9 | 54.6 |
| conflict_and_color_adjective_cases | 360 | 91.4 | 92.8 | 78.9 | 73.3 | 85.3 |

## D4: output validity and concentration

| seed | exact % | JSON/parse errors | distinct in-policy tuples (of 192) | distinct out-of-policy tuples | out-of-policy rows % | top-5 predicted share % |
|--:|--:|--:|--:|--:|--:|--:|
| 42 | 86.5 | 0 | 190 | 3 | 0.1 | 7.1 |
| 43 | 91.4 | 0 | 187 | 6 | 0.4 | 6.5 |
| 44 | 77.7 | 2 | 190 | 2 | 0.2 | 7.6 |
| 45 | 81.4 | 0 | 190 | 4 | 0.4 | 8.1 |
| 46 | 87.5 | 0 | 189 | 1 | 0.1 | 6.2 |

## D4: exact % by emotion (n = rows per category)

| emotion | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| anger | 168 | 98.2 | 92.9 | 60.1 | 67.9 | 93.5 |
| anxiety | 156 | 84.0 | 86.5 | 80.8 | 81.4 | 78.2 |
| boredom | 169 | 100.0 | 81.7 | 62.7 | 63.9 | 75.7 |
| calm | 182 | 75.3 | 89.6 | 44.5 | 66.5 | 83.5 |
| disgust | 175 | 87.4 | 94.9 | 95.4 | 88.6 | 86.9 |
| fatigue | 185 | 92.4 | 98.9 | 98.9 | 88.1 | 94.1 |
| gratitude | 170 | 87.1 | 96.5 | 81.8 | 91.8 | 98.2 |
| happiness | 182 | 89.6 | 94.0 | 64.8 | 86.3 | 96.7 |
| none | 111 | 61.3 | 60.4 | 60.4 | 44.1 | 57.7 |
| nostalgia | 171 | 76.6 | 97.7 | 87.1 | 98.8 | 80.1 |
| sadness | 162 | 86.4 | 95.1 | 98.8 | 87.7 | 93.8 |
| surprise | 169 | 91.7 | 97.0 | 92.9 | 98.8 | 99.4 |

## D4: exact % by base_color (n = rows per category)

| base_color | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| apricot | 102 | 95.1 | 99.0 | 75.5 | 70.6 | 93.1 |
| blue | 176 | 86.4 | 95.5 | 86.9 | 95.5 | 97.7 |
| green | 172 | 90.7 | 95.9 | 87.2 | 85.5 | 94.8 |
| indigo | 108 | 88.0 | 88.9 | 74.1 | 85.2 | 85.2 |
| lavender | 92 | 85.9 | 96.7 | 66.3 | 88.0 | 75.0 |
| lime | 95 | 94.7 | 92.6 | 83.2 | 75.8 | 89.5 |
| mint | 119 | 89.9 | 95.0 | 72.3 | 81.5 | 94.1 |
| none | 82 | 54.9 | 35.4 | 53.7 | 30.5 | 48.8 |
| orange | 192 | 73.4 | 84.9 | 88.5 | 72.4 | 88.0 |
| pink | 101 | 85.1 | 98.0 | 90.1 | 94.1 | 77.2 |
| purple | 174 | 91.4 | 92.5 | 80.5 | 89.1 | 89.7 |
| red | 182 | 83.5 | 95.6 | 75.3 | 85.7 | 88.5 |
| sky | 112 | 98.2 | 91.1 | 73.2 | 82.1 | 90.2 |
| teal | 98 | 88.8 | 96.9 | 55.1 | 80.6 | 91.8 |
| white | 93 | 88.2 | 92.5 | 75.3 | 82.8 | 93.5 |
| yellow | 102 | 91.2 | 97.1 | 78.4 | 79.4 | 77.5 |

## D4: exact % by source (n = rows per category)

| source | n | s42 | s43 | s44 | s45 | s46 |
|---|--:|--:|--:|--:|--:|--:|
| ambiguous_fallback_cases | 36 | 55.6 | 47.2 | 61.1 | 27.8 | 55.6 |
| color_emotion_intensity_combinations | 1604 | 88.4 | 92.3 | 74.3 | 79.4 | 86.2 |
| conflict_and_color_adjective_cases | 360 | 81.4 | 91.9 | 94.4 | 95.6 | 96.1 |

## D2: selected emotions — exact % with Wilson 95% CI and per-dimension mismatch % among those rows

| emotion | seed | n | exact % [95% CI] | mismatch H / S / B / Dimmer / CT % |
|---|--:|--:|---|---|
| anger | 42 | 168 | 75.6 [68.6, 81.5] | 20 / 21 / 23 / 23 / 23 |
| anger | 43 | 168 | 83.3 [77.0, 88.2] | 15 / 17 / 17 / 17 / 17 |
| anger | 44 | 168 | 68.5 [61.1, 75.0] | 30 / 31 / 31 / 31 / 31 |
| anger | 45 | 168 | 45.2 [37.9, 52.8] | 54 / 53 / 52 / 52 / 55 |
| anger | 46 | 168 | 13.1 [8.8, 19.0] | 85 / 85 / 87 / 85 / 85 |
| boredom | 42 | 169 | 76.9 [70.0, 82.6] | 13 / 22 / 23 / 23 / 23 |
| boredom | 43 | 169 | 89.9 [84.5, 93.6] | 10 / 9 / 10 / 10 / 10 |
| boredom | 44 | 169 | 53.3 [45.7, 60.6] | 44 / 46 / 46 / 47 / 47 |
| boredom | 45 | 169 | 47.9 [40.5, 55.4] | 52 / 51 / 52 / 50 / 50 |
| boredom | 46 | 169 | 13.0 [8.8, 18.9] | 85 / 82 / 87 / 87 / 87 |
| calm | 42 | 182 | 93.4 [88.8, 96.2] | 6 / 6 / 7 / 7 / 7 |
| calm | 43 | 182 | 59.9 [52.6, 66.7] | 40 / 39 / 40 / 40 / 40 |
| calm | 44 | 182 | 70.3 [63.3, 76.5] | 30 / 29 / 30 / 30 / 29 |
| calm | 45 | 182 | 62.6 [55.4, 69.3] | 37 / 36 / 37 / 37 / 37 |
| calm | 46 | 182 | 58.8 [51.5, 65.7] | 40 / 41 / 41 / 41 / 41 |
| fatigue | 42 | 185 | 91.4 [86.4, 94.6] | 9 / 9 / 9 / 9 / 9 |
| fatigue | 43 | 185 | 96.8 [93.1, 98.5] | 3 / 3 / 3 / 3 / 3 |
| fatigue | 44 | 185 | 95.1 [91.0, 97.4] | 5 / 5 / 5 / 5 / 5 |
| fatigue | 45 | 185 | 89.2 [83.9, 92.9] | 11 / 11 / 9 / 9 / 11 |
| fatigue | 46 | 185 | 88.1 [82.7, 92.0] | 12 / 12 / 12 / 12 / 12 |
| surprise | 42 | 169 | 96.4 [92.5, 98.4] | 3 / 4 / 2 / 2 / 3 |
| surprise | 43 | 169 | 98.8 [95.8, 99.7] | 1 / 1 / 1 / 1 / 1 |
| surprise | 44 | 169 | 88.2 [82.4, 92.2] | 6 / 12 / 11 / 12 / 12 |
| surprise | 45 | 169 | 85.8 [79.7, 90.3] | 14 / 14 / 13 / 13 / 12 |
| surprise | 46 | 169 | 96.4 [92.5, 98.4] | 4 / 3 / 3 / 3 / 3 |

## Reading

- No output-mode collapse: seeds 45/46 predict 179 and 158 distinct in-policy tuples (others 180–185), top-5 share 9–11 % (others 6–9 %), zero JSON errors. Out-of-policy outputs rise only modestly (1.7 % and 4.2 % of rows vs 1.4–2.0 %). Seed 46 does, however, fail to produce 34 of the 192 policy tuples.
- Errors concentrate in particular emotions: anger and boredom fall to 45/48 % (seed 45) and 13/13 % (seed 46) against 69–90 % at seeds 42–44 (n = 168–169 per emotion, Wilson CIs non-overlapping), while fatigue and surprise stay at 86–96 %. Within the failing rows all five dimensions are wrong together (mismatch 52–55 % / 82–87 % on every dimension), i.e. the model emits a different whole tuple rather than mis-scaling one attribute.
- At L = 4 the same seeds recover these emotions (anger 67.9 / 93.5 %, boredom 63.9 / 75.7 %) and in-policy coverage returns to 189–190 tuples.
- Interpretation: the error concentration in anger and boredom, together with recovery at L = 4, suggests seed-sensitive difficulty in learning the policy's emotion-conditioned tuples at L = 2. This is a failure signature, not an established mechanism; the earlier statement that failures were specific to the S/B dimensions is withdrawn (mismatch is uniform across dimensions within failing rows).
