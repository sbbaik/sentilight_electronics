# Mixed 4/6/8-bit export: what it changes and what it does not (selected d384 L8 V4k)

| quantity | fp32 | mixed-bit | effect | note |
|---|--:|--:|---|---|
| Stored file (MB) | 62.8 | 17.1 | changes | 3.7× smaller: download, OTA update and flash footprint |
| Load time (s) | 0.17 | 0.1 | changes | weights read from disk once; dequantised on load |
| Peak resident memory (MB) | 788 | 665 | unchanged in kind | the model runs at fp32 after load, so RAM is not reduced |
| Median latency (ms, 4 threads) | 98 | 95 | unchanged | same arithmetic at run time |
| p95 latency (ms) | 113 | 105 | unchanged |  |
| Exact match, 300-prompt subset (%) | 85.3 | 86 | within margin | five-seed Δ -0.19 pp, 90 % CI [-0.52, +0.14], TOST ±3 pp pass (S21) |

Reading: the export is a storage-and-distribution measure. It does not lower RAM or latency on this runtime, because weights are restored to fp32 when the model is loaded; the accuracy cost is inside the prospectively fixed ±3-point margin. Where it pays is a storage-constrained or bandwidth-constrained deployment — flash budget, over-the-air updates, cold-start load — not a compute-constrained one.