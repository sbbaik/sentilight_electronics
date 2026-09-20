# Non-generative baselines (240-class prediction of the executable tuple)

Trained on K240 train_100 (49093 rows), C chosen on val; invalid outputs are impossible by construction.

| model | dev test exact % | hold-out exact % | size | CPU median / p95 ms (4 threads) |
|---|--:|--:|---|--:|
| TF-IDF char 2–4-gram + logistic regression | 66.7 | 31.8 | 7.1 MB pickle, 3,650 features | 0.6 / 0.9 |
| SBERT (MiniLM-L12 multilingual, frozen) + logistic regression | 32.8 | 20.5 | encoder 118 M params (nan MB) + head 0.09 M | 7.8 / 8.8 |
| SBERT nearest centroid (no trained head) | 19.9 | 18.2 | encoder 118 M params | 7.7 / 8.7 |

Hold-out exact % by source: {"tfidf_char_logreg": {"holdout_mixed": 21.4, "holdout_color_only": 83.2, "holdout_emotion_only": 39.1, "holdout_fallback": 32.5}, "sbert_logreg": {"holdout_mixed": 20.8, "holdout_color_only": 9.0, "holdout_emotion_only": 29.8, "holdout_fallback": 26.5}}
