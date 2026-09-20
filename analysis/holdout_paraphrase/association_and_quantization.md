# Paraphrase set: lexical overlap, utterance length, and quantization equivalence

## Lexical overlap x utterance length (selected model, 5 seeds)

Exact-tuple match in per cent, with the number of rows per seed in brackets. Cells holding fewer than 30 rows per
seed are marked with an asterisk and should not be read as point estimates.

| lexical overlap | <=25 | 26-45 | 46-65 | >=66 | all lengths |
|---|--:|--:|--:|--:|--:|
| all catalogue wording | 77.9* (19) | 27.6 (50) | 11.7* (24) | 0.0* (2) | 33.1 (95) |
| partial catalogue wording | 25.9 (119) | 8.2 (546) | 4.0 (267) | 1.5 (66) | 8.7 (998) |
| none catalogue wording | 11.1 (133) | 4.1 (523) | 1.1 (227) | 2.5* (24) | 4.3 (907) |

## Association analysis

Logistic regression of row-level correctness on the lexical band, utterance length (centred, in units of ten
characters) and their interaction, with standard errors clustered by action tuple and rows pooled over the five
seeds. Odds ratios are associations in this dataset and are not to be read as causal or independent effects.

| term | odds ratio | 90 % CI | p |
|---|--:|--:|--:|
| Intercept | 0.031 | [0.023, 0.042] | 1.96e-87 |
| C(lex)[T.partial] | 2.428 | [1.757, 3.355] | 6.53e-06 |
| C(lex)[T.all] | 10.236 | [6.669, 15.710] | 4.27e-19 |
| len_c | 0.541 | [0.446, 0.656] | 1.61e-07 |
| C(lex)[T.partial]:len_c | 0.930 | [0.744, 1.164] | 0.596 |
| C(lex)[T.all]:len_c | 0.715 | [0.503, 1.017] | 0.117 |

n = 10,000 rows in 240 action-tuple clusters.

**Reading.** Both lexical overlap and utterance length were associated with accuracy, and neither factor alone
explained the degradation. The two are not experimentally separated in this set, so no independent or causal
effect is claimed for either.

## Quantization equivalence on the paraphrase set

- paired quantized − fp32 by seed: -0.50, -0.05, +0.10, -0.15, +0.00 pp
- mean -0.12 pp, 90 % t CI [-0.34, +0.10]
- TOST at ±3 pp: p = 0.0000 → **equivalence established**

The margin is the one used throughout the prospective register and in the earlier quantization tests, not chosen here.
