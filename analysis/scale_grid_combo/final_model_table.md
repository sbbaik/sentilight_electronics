# Candidate configurations — deployment-facing summary

| Configuration | seeds | params | fp32 weights (MB) | exact % | coarse % | strict % | invalid JSON % | latency mean / p95 (ms) | speed vs deployed |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| W384 (deployed cfg: d384 L8 V24k-prod) | 5 | 23,378,304 | 93.5 | 80.8 ± 3.6 | 85.8 ± 2.7 | 49.3 ± 1.4 | 0.00 | 216 / 234 | 1.00× |
| D4 (d384 L4 V24k-prod) | 5 | 16,297,344 | 65.2 | 81.7 ± 4.9 | 86.1 ± 3.3 | 48.8 ± 1.2 | 0.00 | 118 / 127 | 1.83× |
| V2 V4k (d384 L8 V4k-natural) | 5 | 15,698,304 | 62.8 | 86.5 ± 1.8 | 90.4 ± 1.1 | 51.4 ± 0.6 | 0.00 | 203 / 225 | 1.07× |
| C4kL4 (d384 L4 V4k-natural) | 5 | 8,617,344 | 34.5 | 82.0 ± 6.4 | 86.8 ± 4.8 | 49.2 ± 2.3 | 0.01 | 107 / 114 | 2.03× |
| V2 V4k mixed-4/6/8-bit (KV-cache eval runtime) | 5 | 15,698,304 | 62.8 | 86.3 ± 1.9 | 90.3 ± 1.3 | 51.3 ± 0.8 | 0.00 | 108 / 121 | 2.00× |
| C4kL4 mixed-4/6/8-bit (KV-cache eval runtime) | 5 | 8,617,344 | 34.5 | 81.5 ± 6.1 | 86.5 ± 4.7 | 49.1 ± 2.2 | 0.01 | 58 / 63 | 3.74× |

- Mixed-4/6/8-bit export of C4kL4 (group 64; embedding kept fp32): 12.3 MB on disk vs 34.5 MB fp32 weights.
- Latency is the KV-cache-free 96-step reference decoder (IoTJ Tier 1 protocol); the quantized evaluator dequantizes at load time, so its latency is not a quantization speed measurement.
