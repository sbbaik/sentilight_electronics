# Budget series (B): vocabulary result under a 2× pretraining budget — verdicts

- Launched 2026-09-05 18:03, finished 18:50; 6 runs (B4k, B24k × seeds 42/43/44), 0 failures. Inputs frozen in `budget.inputs.sha256`.
- Identical to V2 V4k / V2 V24k (d = 384, L = 8, natural-corpus tokenizers, K240 SFT 4 epochs, 2,000-row test) except pretraining 4,800 steps instead of 2,400.

## Results (exact tuple match %, mean ± SD over seeds)

| Tokenizer | 2,400 steps (V2) | 4,800 steps (B) | Δ | Pretrain valid loss 2,400 → 4,800 |
|---|--:|--:|--:|--:|
| V4k natural | 86.8 ± 1.4 | 85.9 ± 1.3 | −0.97 (not adopted; seeds −1.2 / +0.2 / −1.8) | 2.39 → 2.12 nats/token (0.94 → 0.83 bits/byte) |
| V24k natural | 68.2 ± 6.1 | 70.6 ± 3.8 | +2.42 (significant, seed-split −2.1 … +8.1; not adopted) | 3.21 → 2.71 nats/token (0.94 → 0.79 bits/byte) |

Per-token losses are not comparable across tokenizers; bits-per-byte (same corpus bytes) are. At 2,400 steps every tokenizer sits at 0.93–0.94 bits/byte, and at 4,800 steps the 24k model is *better* in bits/byte (0.79 vs 0.83) while remaining 15 pp worse downstream — language-model quality on the corpus is not what separates them (`scale_grid_vocab_natural/bits_per_byte.json`).
| **gap V4k − V24k** | +18.6 | **+15.3** (adopted, all seeds +12.1 … +18.4) | | |

Strict / coarse at 4,800 steps: B4k 50.3 / 89.9, B24k 46.4 / 80.4.

## Verdicts

| Prediction | Verdict |
|---|---|
| P-B1: V24k gains ≥ 3 pp more than V4k from doubling | **Met narrowly** (+2.4 vs −1.0 → 3.4 pp difference), but the V24k gain itself fails the seed-sign rule. Rare-token starvation eases slowly: pretraining loss improves by 0.5 nats, yet downstream exact match moves only 2 pp. |
| P-B2: V4k still beats V24k at 4,800 steps by > 5 pp, adopted | **Met.** +15.3 pp exact, +9.5 coarse, +3.8 strict, all three seeds agree. |

## Reading

1. **The vocabulary conclusion is robust to a 2× pretraining step budget.** Doubling steps closes 3 of the 18.6 pp gap. What was doubled is the number of passes over the *same* 35,977 sentences, which adds token occurrences but no new lexical contexts; the rare-token coverage that the test inputs need did not recover. The constraint is corpus diversity and token coverage, not the step count.
2. **V4k is saturated at 2,400 steps.** Its pretraining loss keeps falling (2.39 → 2.12 nats/token; 0.94 → 0.83 bits/byte) but exact match does not move, so the small-vocabulary model's remaining error is not pretraining-optimisation-limited. Together with the sub-additivity in the combined cell this *suggests* an input-side ceiling (~86–89 %), but SFT data limits, label noise, decoding errors and tokenizer segmentation are not excluded; see the error decomposition (`scale_grid_combo/error_decomposition.md`).
3. For the paper, the safe statement is: "Under a fixed 36k-sentence corpus, the 4k tokenizer retained a 15.3-percentage-point advantage over the 24k tokenizer when the pretraining budget was doubled from 2,400 to 4,800 steps." The generalisation that follows is limited: repeating the same small corpus does not supply new lexical diversity and did not restore the rare-token coverage the test inputs require. It does not show that *any* additional pretraining (e.g. on a larger corpus) would fail to help.

## Caveats

- Two vocabularies and one budget multiplier; the full budget–vocabulary surface is not mapped.
- V24k's seed spread (SD 6.1 → 3.8) narrows with budget, consistent with under-trained embeddings being the unstable component.
