# Generic width-search procedures replayed on the completed grids

Rule: step adopted only if all common seeds agree in sign and the mean gain exceeds the seed SD of the differences.

| series | full grid (runs → argmax) | region [256, 384] (runs → argmax) | doubling (runs → chosen, stop) | successive halving (runs → chosen) | adopted in paper |
|---|---|---|---|---|---|
| 24k production tokenizer | 33 → d = 320 | 13 → d = 320 | 15 → d = 192 (stopped at 224) | 10 → d = 320 | d = 384 |
| 4k natural tokenizer | 20 → d = 384 | 15 → d = 384 | 10 → d = 224 (stopped at 256) | 6 → d = 320 | d = 384 |
