# End-to-end software-path measurement with an emulated device

evaluation workstation, service and client on the same host (loopback); selected d384 L8 V4k, mixed 4/6/8-bit export, seed 42; 4 threads; device: Tasmota HTTP emulator on the same host, no added delay (tools/e2e/tasmota_emulator.py).

| mode | n | service round trip median / p95 (ms) | inside service | emulated device | client total (admitted) | withheld | raw identical to evaluation | exact % |
|---|--:|---|---|---|---|--:|--:|--:|
| raw_text | 235 | 106.6 / 112.3 | 101.3 / 106.6 | 3.5 / 5.0 | 110.0 / 116.7 (n = 208) | 27 / 240 | 240 / 240 | 28.3 |
| wrapper | 235 | 97.2 / 102.9 | 91.8 / 96.8 | 3.5 / 5.0 | 100.6 / 107.1 (n = 194) | 42 / 240 | 145 / 240 | 27.5 |

Not included: the Wi-Fi hop to the bulb, the bulb firmware's response and the physical light transition.
