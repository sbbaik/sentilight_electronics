# Vocabulary series — results and verdicts (V2, natural-corpus tokenizers; V1 as negative control)

- V2 launched 2026-09-05 15:53, finished 17:16; 12 runs, 0 failures. Inputs frozen in `vocab_series.inputs.sha256`.
- Backbone d = 384, L = 8 for every vocabulary; pretrain 2,400 steps on the same clean corpus (re-encoded per tokenizer); SFT 4 epochs on K240 policy-only + fill; eval on K240 `test_rule.jsonl` (2,000 rows). Seeds 42/43/44.
- Tokenizers: ByteLevel BPE (same recipe as production) trained on the 35,977 natural KOTE lines of the corpus (`tools/build_vocab_series.py --tokenizer-corpus natural`). V1 = same recipe trained on the whole template-heavy corpus. Reference = production 24k tokenizer (W384).

## Results (exact tuple match %, mean ± SD; strict / coarse in the second block)

| Tokenizer | Vocab | Params | Emb. share | Exact % | Strict % | Coarse % | Test tokens with <100 pretrain occurrences |
|---|--:|--:|--:|--:|--:|--:|--:|
| **V2 V4k** | 4,000 | 15.7M | 10 % | **86.8 ± 1.4** | 51.1 ± 0.1 | 90.3 ± 0.4 | 0.1 % |
| V2 V8k | 8,000 | 17.2M | 18 % | 82.1 ± 3.3 | 49.3 ± 1.1 | 87.0 ± 2.1 | 3.5 % |
| V2 V16k | 16,000 | 20.3M | 30 % | 70.9 ± 1.7 | 45.5 ± 1.0 | 79.3 ± 2.5 | 10.7 % |
| V2 V24k | 24,000 | 23.4M | 39 % | 68.2 ± 6.1 | 44.5 ± 2.0 | 78.3 ± 4.6 | 17.6 % |
| production 24k (W384) | 24,000 | 23.4M | 39 % | 79.1 ± 1.3 | 49.3 ± 0.2 | 84.9 ± 0.6 | 10.1 % |
| V1 V4k (full corpus) | 4,000 | 15.7M | 10 % | 53.3 ± 4.5 | 39.2 | 65.2 | 3.7 % (+13 % byte fragments) |
| V1 V24k (full corpus) | 24,000 | 23.4M | 39 % | 58.5 ± 3.5 | 38.9 | 67.6 | 30.1 % (+6 % byte fragments) |

Row-level McNemar (Stouffer over seeds, Holm over 24 tests, sign rule):

| Contrast | Exact Δ pp | Verdict |
|---|--:|---|
| V2 V4k → V8k | −4.68 | adopted (smaller is better) |
| V2 V8k → V16k | −11.25 | adopted |
| V2 V16k → V24k | −2.72 | significant but seed-split |
| production 24k → V2 V24k | −10.92 | adopted (retrained 24k is worse) |
| V1 → V2, same size (4k / 8k / 16k / 24k) | +33.5 / +29.3 / +24.8 / +9.7 | all adopted, all seeds agree |

## Verdicts on the preregistered predictions

| Prediction | Verdict |
|---|---|
| P-V1: flat from V8k to V24k | **Rejected.** Accuracy falls monotonically with vocabulary size; V8k → V24k is −13.9 pp exact. |
| P-V2: V4k not worse than V8k; any drop is at V4k | **Met, and inverted.** V4k is *better* than V8k (+4.7 pp, adopted). No drop at the small end. |
| P-V3: retrained V24k ≥ production 24k | **Rejected.** The production tokenizer is 10.9 pp better than a 24k tokenizer trained on 36k natural lines. Its 62 % higher token count on the corpus is not a defect; its merges are supported by a far larger training text. |
| P-V4: V2 beats V1 at every size, gap shrinks with size | **Met.** +33.5 → +9.7 pp exact, all seeds agree. |

## Mechanism

Two failure modes bracket the vocabulary step:

1. **Template over-merging (V1).** BPE trained on the task corpus turns training-template words into single tokens; unseen phrasings shatter into byte fragments (6–13 % of test tokens). Validation loss does not see this because validation shares the training templates.
2. **Rare-token starvation (V2, large V).** With only 36k natural lines and 2,400 pretraining steps, a larger vocabulary spends its capacity on merges that occur too rarely to train: the share of test tokens seen fewer than 100 times in pretraining rises from 0.1 % (4k) to 17.6 % (24k) and tracks the accuracy decline exactly. Fewer tokens per line (15.4 vs 20.3) buys nothing when the tokens themselves are under-trained.

The production tokenizer sits between the two: broad-corpus merges (10 % rare-token share) that behave almost like syllables on this domain.

## Implications for the sizing recipe (Section 3.3, vocabulary step)

- For a small domain model whose tokenizer corpus is tens of thousands of sentences, choose the vocabulary by **token coverage and exposure**, not compression: at this pretraining budget the near-syllable 4k vocabulary wins outright and cuts the embedding term from 39 % to 10 % of parameters. (Per-token pretraining losses across tokenizers are not comparable; in bits/byte all four are 0.93–0.94 at 2,400 steps.)
- Train the tokenizer on natural text, never on the SFT/template corpus; check two cheap diagnostics before training any model: byte-fragment share on held-out phrasings (should be ≈ production's 3 %, not 6–13 %) and share of held-out tokens with < 100 pretraining occurrences (should be a few percent).
- **Best configuration found in the whole study: d = 384, L = 8, V = 4k (natural), 15.7M parameters, 86.8 % exact / 90.3 % coarse**, versus the deployed 23.4M model at 79.1 % / 84.9 %. Combined with the depth result (L = 4 ≈ L = 8 in accuracy at half the latency), a ~12M-parameter model (d = 384, L = 4, V = 4k) is the natural next check.

## Caveats

- **Scope statement for the paper:** the vocabulary finding is conditioned on a 36k-sentence natural corpus and the tested step budgets (2,400 and 4,800 steps). Whether a larger natural corpus restores 24k is a separate research axis and is not claimed either way.
- Vocabulary interacts with pretraining budget: with more steps or a larger natural corpus, larger vocabularies would likely recover. The result is for 2,400 steps × 64 × 256 positions on a 36k-line natural corpus and should be stated with that budget.
- Korean-specific: syllable-level tokens are unusually well suited to Korean morphology; the direction may differ for other languages.
- Single width and depth (384 / 8); the V4k advantage at other (d, L) is untested (see next check above).
- V2 V24k has the largest seed spread (SD 6.1), consistent with under-trained embeddings.
