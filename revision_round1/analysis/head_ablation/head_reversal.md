# Why the head loses on the audited set

## 1. Audited set: attribute-level reading (5 seeds pooled)

| model | form | exact % | colour right | emotion right | intensity right | out of catalogue | distinct classes | top-class share |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| decoder | plain | 35.3 | 76.2 | 59.2 | 62.0 | 6.7 | 156 | 3.0 % |
| decoder | negation | 14.5 | 40.5 | 46.0 | 49.0 | 15.0 | 66 | 7.6 % |
| decoder | word_order | 9.0 | 21.5 | 50.5 | 39.5 | 13.0 | 59 | 9.8 % |
| decoder | context_clause | 20.0 | 66.0 | 43.5 | 54.0 | 8.0 | 83 | 4.9 % |
| decoder | all | 24.9 | 59.4 | 52.9 | 54.8 | 9.3 | 185 | 2.9 % |
| head | plain | 19.3 | 55.8 | 48.0 | 54.8 | 0.0 | 132 | 6.3 % |
| head | negation | 5.0 | 47.5 | 51.5 | 34.0 | 0.0 | 67 | 7.5 % |
| head | word_order | 12.5 | 70.5 | 15.5 | 59.0 | 0.0 | 48 | 11.5 % |
| head | context_clause | 4.0 | 29.5 | 30.5 | 48.0 | 0.0 | 59 | 15.0 % |
| head | all | 13.2 | 52.5 | 40.2 | 50.9 | 0.0 | 167 | 7.1 % |

Head prediction concentration on the paper's sets: development: 233 classes, top share 2.5 %; unseen_frames: 240 classes, top share 2.7 %; stress: 237 classes, top share 5.4 %

## 2. Development test with a neutral clause (same 2,000 requests; exact %, 5 seeds)

| model | original | clause before | clause after | long clause before | Δ before | Δ after | Δ long before |
|---|--:|--:|--:|--:|--:|--:|--:|
| head | 87.17 ± 0.68 | 28.56 ± 18.39 | 81.52 ± 1.09 | 21.06 ± 18.32 | -58.6 [-75.7, -41.5] (5/5 −) | -5.7 [-7.3, -4.0] (5/5 −) | -66.1 [-83.9, -48.3] (5/5 −) |
| decoder | 86.54 ± 1.81 | 70.37 ± 5.06 | 6.7 ± 2.2 | 76.45 ± 6.1 | -16.2 [-20.7, -11.7] (5/5 −) | -79.8 [-83.2, -76.5] (5/5 −) | -10.1 [-15.3, -4.8] (5/5 −) |
