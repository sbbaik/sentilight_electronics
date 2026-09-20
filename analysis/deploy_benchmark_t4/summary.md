# CPU deployment benchmark, 4 torch threads (production runtime compact_llm_q4/inference.py, KV-cache greedy decoding, device=cpu)

- Host: shared workstation (Intel Core Ultra 9 285K, 24 cores) with other users' jobs running; load average recorded in host_load_at_*.txt. Threads pinned to 4 because the 24-thread default produced multi-second tails under contention (see ../deploy_benchmark/summary.md).
- 300 timed prompts after 20 warm-up (deterministic subset of the K240 test set), one fresh process per model. Accuracy columns are on this 300-prompt subset only.

| Model | file MB | load s | RSS after load MB | peak RSS MB | median ms | p95 ms | mean ms | invalid JSON | exact % | coarse % |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 운영 fp32 23.4M (production lineage) | 93.5 | 0.21 | 638 | 724 | 107 | 126 | 109 | 0.3% | 58.0 | 72.3 |
| 운영 mixed4 23.4M (production lineage) | 47.8 | 0.20 | 691 | 728 | 101 | 108 | 102 | 0.3% | 57.3 | 71.0 |
| W384 fp32 23.4M | 280.6 | 0.29 | 674 | 904 | 104 | 122 | 107 | 0.0% | 76.3 | 86.0 |
| W384 mixed4 23.4M | 47.8 | 0.20 | 691 | 729 | 101 | 110 | 101 | 0.0% | 77.0 | 87.0 |
| V2 V4k fp32 15.7M | 188.5 | 0.17 | 632 | 788 | 98 | 113 | 100 | 0.0% | 85.3 | 91.0 |
| V2 V4k mixed4 15.7M | 17.1 | 0.10 | 658 | 665 | 95 | 105 | 95 | 0.0% | 86.0 | 90.3 |
| C4kL4 mixed4 8.6M | 12.3 | 0.07 | 590 | 598 | 52 | 70 | 53 | 0.0% | 79.3 | 84.7 |
