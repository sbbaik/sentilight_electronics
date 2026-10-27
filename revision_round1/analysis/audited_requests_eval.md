# Audited request set: evaluation summary

240 rows (sha256 ce8b84279b21a23e…); {'word_order': 40, 'negation': 40, 'plain': 120, 'context_clause': 40}; mean length (chars) {'plain': 34.2, 'negation': 40.6, 'word_order': 36.4, 'context_clause': 66.4}.
Drafting: GPT-6 Astra (OpenAI), called 21 October 2026, one sentence per cell under a fixed brief. Audit: every sentence read, corrected where needed and annotated by the first author; policy gold = catalogue tuple of the cell.

## Families (five seeds unless stated)

| model | exact % | 90% t CI | coarse % | valid output % | gate withheld % | correct withheld | wrong withheld (% of wrong) | wrong passed (% of all) |
|---|--:|---|--:|--:|--:|--:|--:|--:|
| Selected generative decoder, fp32 (15.7 M) | 24.92 ± 0.54 | [24.4, 25.43] | 40.17 ± 1.16 | 100 | 9.33 ± 4.17 | 0 | 12.43 ± 5.56 | 65.75 ± 4.26 |
| Selected generative decoder, mixed 4/6/8-bit | 24.75 ± 2.1 | [22.75, 26.75] | 39.25 ± 2.29 | 100 | 10.5 ± 3.68 | 0 | 13.99 ± 4.98 | 64.75 ± 4.7 |
| Retrained deployed architecture (23.4 M, 24k tokenizer) | 17.08 ± 0.88 | [16.24, 17.93] | 35.58 ± 2.26 | 100 | 2.25 ± 0.76 | 0 | 2.72 ± 0.94 | 80.67 ± 1.6 |
| Size-matched 240-class head (15.8 M) | 13.25 ± 2.8 | [10.58, 15.92] | 28.75 ± 2.3 | 100 | 0.0 ± 0.0 | 0 | 0.0 ± 0.0 | 86.75 ± 2.8 |

## Exact % by request variation, all families

| model | plain | negation | word_order | context_clause |
|---|--:|--:|--:|--:|
| Selected generative decoder, fp32 (15.7 M) | 35.33 ± 1.83 | 14.5 ± 5.42 | 9.0 ± 4.87 | 20.0 ± 2.5 |
| Selected generative decoder, mixed 4/6/8-bit | 35.17 ± 2.91 | 12.0 ± 4.11 | 9.5 ± 4.81 | 21.5 ± 2.85 |
| Retrained deployed architecture (23.4 M, 24k tokenizer) | 24.17 ± 2.28 | 6.5 ± 1.37 | 5.0 ± 3.95 | 18.5 ± 4.87 |
| Size-matched 240-class head (15.8 M) | 19.33 ± 5.12 | 5.0 ± 3.95 | 12.5 ± 2.5 | 4.0 ± 2.24 |

## Paired seed contrasts (percentage points)

- head_minus_decoder: mean -11.66, 90% CI [-13.89, -9.43], 95% CI [-14.57, -8.76], seeds +0/−5; per seed [-8.33, -14.58, -12.91, -11.67, -10.83]
- mixed_minus_fp32: mean -0.16, 90% CI [-1.69, 1.36], 95% CI [-2.15, 1.82], seeds +1/−3; per seed [2.5, 0.0, -1.66, -0.83, -0.83]
- selected_minus_reference: mean +7.83, 90% CI [6.53, 9.13], 95% CI [6.13, 9.53], seeds +5/−0; per seed [10.0, 6.66, 7.91, 7.92, 6.66]

## Selected model (fp32), breakdowns

### Variation

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| plain | 120 | 35.33 ± 1.83 | [33.59, 37.07] |
| word_order | 40 | 9.0 ± 4.87 | [4.35, 13.65] |
| negation | 40 | 14.5 ± 5.42 | [9.33, 19.67] |
| context_clause | 40 | 20.0 ± 2.5 | [17.62, 22.38] |

### Colour named vs omitted

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| named | 210 | 25.05 ± 0.87 | [24.22, 25.87] |
| omitted | 30 | 24.0 ± 3.65 | [20.52, 27.48] |

### Colour value

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| red | 30 | 28.0 ± 3.8 | [24.38, 31.62] |
| blue | 30 | 31.33 ± 6.06 | [25.56, 37.11] |
| purple | 30 | 30.0 ± 7.07 | [23.26, 36.74] |
| white | 30 | 20.67 ± 5.48 | [15.44, 25.89] |
| orange | 30 | 20.67 ± 4.35 | [16.52, 24.81] |
| yellow | 30 | 28.67 ± 5.06 | [23.85, 33.49] |
| none | 30 | 24.0 ± 3.65 | [20.52, 27.48] |
| green | 30 | 16.0 ± 4.35 | [11.86, 20.14] |

### Emotion named vs omitted

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| named | 200 | 24.2 ± 1.35 | [22.91, 25.49] |
| omitted | 40 | 28.5 ± 6.27 | [22.52, 34.48] |

### Emotion value

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| calm | 40 | 22.0 ± 6.22 | [16.06, 27.94] |
| none | 40 | 28.5 ± 6.27 | [22.52, 34.48] |
| sadness | 40 | 29.5 ± 5.42 | [24.33, 34.67] |
| anger | 40 | 31.5 ± 4.54 | [27.17, 35.83] |
| anxiety | 40 | 18.5 ± 4.87 | [13.85, 23.15] |
| happiness | 40 | 19.5 ± 7.79 | [12.08, 26.92] |

### Intensity value

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| bright | 48 | 17.5 ± 2.8 | [14.83, 20.16] |
| strong | 48 | 17.08 ± 2.72 | [14.49, 19.67] |
| dark | 48 | 13.75 ± 7.88 | [6.24, 21.26] |
| soft | 48 | 31.25 ± 3.29 | [28.11, 34.39] |
| neutral | 48 | 45.0 ± 5.43 | [39.82, 50.18] |

### Intensity neutral vs non-neutral

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| non-neutral | 192 | 19.9 ± 1.7 | [18.27, 21.52] |
| neutral | 48 | 45.0 ± 5.43 | [39.82, 50.18] |

### Omission pattern

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| colour and emotion named | 175 | 23.66 ± 1.32 | [22.4, 24.91] |
| emotion omitted | 35 | 32.0 ± 7.93 | [24.44, 39.56] |
| colour omitted | 25 | 28.0 ± 2.83 | [25.3, 30.7] |
| both omitted | 5 | 4.0 ± 8.94 | [-4.53, 12.53] |

### Negation rows vs plain rows of the same intensities ['bright', 'dark', 'soft', 'strong']

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| negation | 40 | 14.5 ± 5.42 | [9.33, 19.67] |
| plain, same intensities | 96 | 29.17 ± 2.08 | [27.18, 31.15] |

### Length tertiles (chars; cuts [33.7, 44.0])

| group | rows | exact % (5 seeds) | 90% CI |
|---|--:|--:|---|
| medium | 84 | 25.0 ± 3.15 | [22.0, 28.0] |
| short | 80 | 32.25 ± 3.47 | [28.94, 35.56] |
| long | 76 | 17.11 ± 1.61 | [15.57, 18.64] |

### Attribute wrong among wrong outputs (%)

{"colour": 41.6, "emotion": 50.3, "intensity": 47.8, "out_of_catalogue": 12.4, "wrong_outputs_over_seeds": 901}

Rows carrying an audit note: 16, exact 31.25 ± 4.42
