# Vocabulary series build

- Corpus: `backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1/pretrain_corpus.txt` (245,258 lines)

- Tokenizer training text: `backend/models/compact_llm/tokenizer_vocab_series_natural/_tokenizer_training_lines.txt` (35,977 lines, mode natural)

| Tokenizer | Vocab | Pretrain tokens | Tokens/line | SFT len p99 | >256 | Test tok/line | Test frag % | Train tok/line | Test/train |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| V24k-orig | 24,000 | 5,145,967 | 20.98 | 164 | 0 | 17.33 | 2.9 | 11.82 | 1.467 |
| V4k | 4,000 | 5,663,473 | 23.09 | 220 | 0 | 20.3 | 3.6 | 14.26 | 1.423 |
| V8k | 8,000 | 5,071,976 | 20.68 | 199 | 0 | 18.74 | 1.1 | 12.92 | 1.451 |
| V16k | 16,000 | 4,538,123 | 18.5 | 184 | 0 | 16.74 | 0.4 | 10.92 | 1.534 |
| V24k | 24,000 | 4,212,985 | 17.18 | 173 | 0 | 15.41 | 0.3 | 9.92 | 1.554 |
