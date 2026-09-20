# Vocabulary series V1 (tokenizers trained on the full pretraining corpus) — negative control

- Launched 2026-09-05 14:29, finished 15:52; 12 runs (V4k/V8k/V16k/V24k × seeds 42/43/44), 0 failures
- d = 384, L = 8, pretrain 2,400 steps on the clean corpus, SFT 4 epochs on K240 policy-only + fill, eval on K240 `test_rule.jsonl`
- Reference: W384 = production 24k tokenizer, identical backbone and data

## Results (mean ± SD over seeds)

| Tokenizer | Vocab | Params | Strict % | Coarse % | Exact tuple % |
|---|--:|--:|--:|--:|--:|
| V4k (full corpus) | 4,000 | 15.7M | 39.2 ± 2.9 | 65.2 ± 4.4 | 53.3 ± 4.5 |
| V8k (full corpus) | 8,000 | 17.2M | 39.1 ± 1.2 | 64.3 ± 0.2 | 52.8 ± 2.4 |
| V16k (full corpus) | 16,000 | 20.3M | 33.9 ± 2.0 | 57.8 ± 3.3 | 46.1 ± 4.1 |
| V24k (full corpus) | 24,000 | 23.4M | 38.9 ± 0.5 | 67.6 ± 2.5 | 58.5 ± 3.5 |
| **W384 (production 24k)** | 24,000 | 23.4M | **49.3 ± 0.2** | **84.9 ± 0.6** | **79.1 ± 1.3** |

Every retrained tokenizer loses 17–27 pp coarse and 21–33 pp exact against the production tokenizer of the same backbone. The loss does not shrink with vocabulary size (V24k retrained: −20.6 pp exact), so this is not a vocabulary-size effect.

## Diagnosis

SFT validation loss is unchanged (0.0012–0.0016 vs 0.0016), so the models fit the training templates as well as before; they fail only on the test templates. The pretraining corpus (245,258 lines) contains just 60,940 unique lines: about 36,000 natural KOTE sentences plus repeated SFT template sentences. BPE trained on it merges whole template words into single tokens, so training inputs compress to ~7 tokens/line, while unseen test-template words fall back to byte fragments.

| Tokenizer | Test tokens/line | Test byte-fragment share | Train tokens/line | Test/train ratio |
|---|--:|--:|--:|--:|
| production 24k | 17.3 | 2.9 % | 11.8 | 1.47 |
| V1 V4k | 16.4 | 13.2 % | 7.6 | 2.16 |
| V1 V8k | 14.7 | 7.9 % | 7.2 | 2.03 |
| V1 V16k | 13.5 | 6.2 % | 7.0 | 1.93 |
| V1 V24k | 12.9 | 6.4 % | 6.9 | 1.87 |
| V2 V8k (natural lines only) | 18.7 | 1.1 % | 12.9 | 1.45 |
| V2 V24k (natural lines only) | 15.4 | 0.3 % | 9.9 | 1.55 |

The production tokenizer behaves almost like a syllable tokenizer for Korean (e.g. 정돈해줘 → 정/돈/해/줘), which is template-agnostic. Tokenizers trained only on the 35,977 natural lines reproduce that behaviour (test/train ratio 1.42–1.55, fragments ≤ 3.6 %); this is the V2 design (`tokenizer_vocab_series_natural/`).

## What this contributes to the paper

1. **Tokenizer provenance dominates vocabulary size** at this scale. A 24k tokenizer trained on the task corpus is 21 pp worse than a 24k tokenizer trained on broad text; V4k vs V24k within V1 differs by only 5 pp.
2. **Do not train the tokenizer on the SFT/template corpus.** Byte-fragment share on held-out phrasing (here 6–13 % vs 3 %) is a cheap pre-training diagnostic that predicted the failure before any model was trained; the sizing recipe should include it as a check on the vocabulary step.
3. The production tokenizer's inefficiency on the corpus (21 tokens/line vs 13 for a corpus-trained 24k) is the *price* of robustness, not a defect. Compression on the training distribution is the wrong objective for a tokenizer that must generalise across phrasings.

## Caveats

- Pretraining is step-matched, so V1 models saw 10–12 corpus passes vs 7.6 for the production tokenizer; more passes did not help, which argues against under-training as the cause.
- The test set's templates differ from the training templates by construction (that is the benchmark's purpose); a benchmark that reused training templates would have hidden this failure entirely, as the SFT validation loss did.
