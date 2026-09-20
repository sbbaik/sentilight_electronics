# Error decomposition (rates in %, pooled over seeds)

- Runs: C4kL4, V2V4k, D4, W384; seeds [42, 43, 44]

## By source layer

| group | n/seed | C4kL4 exact / coarse | V2V4k exact / coarse | D4 exact / coarse | W384 exact / coarse |
|---|--:|--:|--:|--:|--:|
| color_emotion_intensity_combinations | 1420 | 87.7 / 91.2 | 89.3 / 92.4 | 85.5 / 89.2 | 78.0 / 84.8 |
| conflict_and_color_adjective_cases | 400 | 82.3 / 88.5 | 80.3 / 86.5 | 83.0 / 88.3 | 82.8 / 87.3 |
| ambiguous_fallback_cases | 180 | 77.0 / 78.1 | 81.9 / 81.9 | 73.7 / 73.9 | 79.3 / 80.4 |

## By input structure

| group | n/seed | C4kL4 exact / coarse | V2V4k exact / coarse | D4 exact / coarse | W384 exact / coarse |
|---|--:|--:|--:|--:|--:|
| colour + emotion | 326 | 81.2 / 87.5 | 83.1 / 90.4 | 72.1 / 79.4 | 68.6 / 80.3 |
| colour + emotion + intensity | 1260 | 91.2 / 93.9 | 92.5 / 94.9 | 91.7 / 94.2 | 83.8 / 88.5 |
| colour + no-emotion | 31 | 67.7 / 78.5 | 58.1 / 66.7 | 64.5 / 76.3 | 71.0 / 80.6 |
| colour + no-emotion + intensity | 106 | 72.6 / 84.3 | 70.4 / 78.9 | 72.6 / 83.3 | 80.5 / 88.4 |
| no-colour + emotion | 18 | 27.8 / 42.6 | 37.0 / 53.7 | 24.1 / 38.9 | 31.5 / 46.3 |
| no-colour + emotion + intensity | 76 | 72.8 / 74.6 | 66.2 / 67.5 | 68.9 / 71.1 | 58.3 / 61.8 |
| no-colour + no-emotion | 39 | 32.5 / 37.6 | 41.9 / 41.9 | 25.6 / 25.6 | 56.4 / 61.5 |
| no-colour + no-emotion + intensity | 144 | 89.1 / 89.1 | 93.1 / 93.1 | 86.3 / 86.6 | 85.6 / 85.6 |

## By colour

| group | n/seed | C4kL4 exact / coarse | V2V4k exact / coarse | D4 exact / coarse | W384 exact / coarse |
|---|--:|--:|--:|--:|--:|
| (none) | 277 | 72.7 / 74.8 | 74.8 / 76.3 | 69.0 / 70.6 | 70.5 / 73.2 |
| blue | 271 | 92.4 / 94.3 | 92.0 / 94.2 | 86.8 / 88.6 | 82.5 / 86.5 |
| green | 215 | 86.8 / 88.5 | 83.1 / 85.7 | 83.9 / 86.7 | 76.4 / 80.8 |
| orange | 208 | 83.8 / 92.6 | 87.0 / 94.6 | 84.8 / 90.4 | 77.7 / 89.7 |
| purple | 228 | 89.8 / 91.1 | 95.6 / 95.6 | 89.8 / 91.5 | 84.6 / 86.8 |
| red | 299 | 90.2 / 93.5 | 86.7 / 92.6 | 89.4 / 93.3 | 86.0 / 90.0 |
| white | 220 | 79.2 / 87.4 | 84.7 / 90.0 | 81.2 / 91.1 | 71.7 / 86.5 |
| yellow | 282 | 89.4 / 93.4 | 90.9 / 94.1 | 86.8 / 90.4 | 81.2 / 86.5 |

## By emotion

| group | n/seed | C4kL4 exact / coarse | V2V4k exact / coarse | D4 exact / coarse | W384 exact / coarse |
|---|--:|--:|--:|--:|--:|
| (none) | 320 | 74.7 / 80.2 | 75.9 / 79.6 | 72.3 / 77.1 | 79.0 / 83.1 |
| anger | 328 | 93.1 / 97.0 | 91.4 / 95.9 | 89.9 / 95.1 | 92.9 / 97.0 |
| anxiety | 335 | 86.9 / 88.6 | 89.8 / 90.7 | 82.9 / 84.8 | 80.7 / 83.4 |
| calm | 335 | 82.8 / 86.4 | 91.0 / 92.5 | 83.9 / 87.1 | 67.2 / 72.8 |
| happiness | 333 | 87.9 / 95.0 | 88.2 / 95.1 | 86.3 / 93.1 | 70.1 / 87.7 |
| sadness | 349 | 88.3 / 89.4 | 84.3 / 87.7 | 87.7 / 88.4 | 84.7 / 85.8 |

## By intensity

| group | n/seed | C4kL4 exact / coarse | V2V4k exact / coarse | D4 exact / coarse | W384 exact / coarse |
|---|--:|--:|--:|--:|--:|
| bright | 408 | 83.8 / 90.3 | 87.8 / 92.4 | 86.6 / 92.2 | 83.1 / 91.6 |
| dark | 333 | 91.7 / 93.0 | 91.5 / 92.7 | 88.5 / 90.4 | 79.0 / 82.2 |
| neutral | 414 | 73.3 / 80.2 | 75.4 / 82.4 | 65.1 / 72.4 | 66.0 / 77.1 |
| soft | 469 | 92.3 / 92.8 | 89.1 / 90.5 | 88.9 / 90.0 | 79.8 / 81.7 |
| strong | 376 | 87.8 / 91.5 | 91.3 / 94.3 | 91.5 / 94.1 | 88.3 / 92.9 |

## Most frequent failing dimension among coarse failures

| run | H | S | B | Dimmer | CT | coarse failures/seed |
|---|--:|--:|--:|--:|--:|--:|
| C4kL4 | 111 | 354 | 315 | 214 | 182 | 211 |
| V2V4k | 162 | 327 | 251 | 170 | 164 | 194 |
| D4 | 91 | 381 | 420 | 281 | 233 | 247 |
| W384 | 98 | 499 | 442 | 289 | 249 | 301 |

## Output validity

| run | rows/seed | invalid or missing prediction (%) | exact ∧ ¬strict (%) | strict ∧ ¬exact (%) |
|---|--:|--:|--:|--:|
| C4kL4 | 2000 | 0.02 | 37.67 | 2.67 |
| V2V4k | 2000 | 0.00 | 38.68 | 2.97 |
| D4 | 2000 | 0.00 | 37.42 | 2.97 |
| W384 | 2000 | 0.00 | 34.25 | 4.50 |
