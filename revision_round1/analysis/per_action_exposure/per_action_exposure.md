# Per-action training exposure and policy reproduction

240 cells; training rows per cell min 18, median 234, mean 204.6, max 340.

## development

Spearman ρ (exposure vs exact) = +0.289

| exposure quartile | cells | rows/cell | mean exact % |
|---|--:|---|--:|
| Q1 (lowest) | 60 | 18–214 | 65.6 |
| Q2 | 64 | 216–234 | 91.4 |
| Q3 | 61 | 235–252 | 87.1 |
| Q4 (highest) | 55 | 254–340 | 89.1 |

### 5 least-exposed cells

| colour | emotion | intensity | train rows | exact % (5 seeds) | 90 % interval |
|---|---|---|--:|--:|---|
| none | none | neutral | 18 | 48.7 | [26.7, 70.7] |
| none | anxiety | neutral | 27 | 50.0 | [16.3, 83.7] |
| none | sadness | neutral | 31 | 25.0 | [8.1, 41.9] |
| none | anger | neutral | 37 | 20.0 | [-6.1, 46.1] |
| none | calm | neutral | 37 | 50.0 | [16.3, 83.7] |

## unseen_frames

Spearman ρ (exposure vs exact) = -0.158

| exposure quartile | cells | rows/cell | mean exact % |
|---|--:|---|--:|
| Q1 (lowest) | 60 | 18–214 | 66.1 |
| Q2 | 64 | 216–234 | 57.6 |
| Q3 | 61 | 235–252 | 56.3 |
| Q4 (highest) | 55 | 254–340 | 56.7 |

### 5 least-exposed cells

| colour | emotion | intensity | train rows | exact % (5 seeds) | 90 % interval |
|---|---|---|--:|--:|---|
| none | none | neutral | 18 | 40.0 | [15.0, 65.0] |
| none | anxiety | neutral | 27 | 60.0 | [46.9, 73.1] |
| none | sadness | neutral | 31 | 45.0 | [29.0, 61.0] |
| none | anger | neutral | 37 | 56.0 | [27.7, 84.3] |
| none | calm | neutral | 37 | 62.5 | [45.6, 79.4] |
