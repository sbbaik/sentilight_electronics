# -*- coding: utf-8 -*-
"""Consolidate the emulated-bulb end-to-end measurement into analysis/e2e_simulated/e2e_summary.{json,md}.

Two service configurations were measured on the same host with the same checkpoint (selected mixed 4/6/8-bit,
seed 42, four CPU threads): `raw_text` (the adapter hands the request to the model's own prompt builder, i.e. the
evaluation condition) and `wrapper` (the service's default COMPACTLM_JSON_PROMPT wrapper). The device is a Tasmota
emulator on the same host with no added delay, so the Wi-Fi hop and the bulb firmware are NOT in these numbers.
"""
from __future__ import annotations

import collections
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
D = HERE / "analysis/e2e_simulated"
STORED = HERE / "analysis/audited_eval/per_row/selected_V4k_L8_mixed4_s42.jsonl"


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def stats(xs):
    xs = [x for x in xs if x is not None]
    return {"n": len(xs), "median_ms": round(st.median(xs), 1), "p95_ms": round(pct(xs, 0.95), 1), "max_ms": round(max(xs), 1)} if xs else None


def main():
    stored = {r["input"]: r for r in (json.loads(l) for l in STORED.open(encoding="utf-8"))}
    out = {"host": "evaluation workstation, service and client on the same host (loopback)", "threads": 4,
           "checkpoint": "selected d384 L8 V4k, mixed 4/6/8-bit export, seed 42",
           "device": "Tasmota HTTP emulator on the same host, no added delay (tools/e2e/tasmota_emulator.py)",
           "requests": "the 240 audited requests in file order; first 5 are warm-up and excluded", "modes": {}}
    for mode in ("raw_text", "wrapper"):
        A = [json.loads(l) for l in (D / f"e2e_emulated_bulb_{mode}.jsonl").open(encoding="utf-8")]
        M = [r for r in A if not r["warmup"]]
        S = json.loads((D / f"e2e_emulated_bulb_{mode}_summary.json").read_text(encoding="utf-8"))
        by = collections.defaultdict(list)
        for r in M:
            by[r["variation"]].append(r)
        out["modes"][mode] = {
            "measured_at_utc": S["measured_at_utc"], "n_measured": len(M),
            "service_round_trip_ms": stats([r["t_service_ms"] for r in M]),
            "service_internal_ms": stats([r["service_internal_latency_ms"] for r in M]),
            "emulated_device_reply_ms": stats([r.get("t_bulb_ms") for r in M]),
            "client_total_ms_admitted_requests": stats([r.get("t_total_ms") for r in M]),
            "http_overhead_median_ms": round(st.median(r["t_service_ms"] - r["service_internal_latency_ms"] for r in M), 1),
            "withheld_by_gate": sum(r["lighting"] is None for r in A), "withheld_pct": round(100 * sum(r["lighting"] is None for r in A) / len(A), 1),
            "raw_identical_to_stored_evaluation": sum(r.get("raw") == stored[r["input"]]["predicted"] for r in A), "rows": len(A),
            "exact_vs_gold_pct_all_240": round(100 * st.mean(r["exact_vs_gold"] for r in A), 1),
            "device_ok_rate_pct": S["bulb_ok_rate"], "readback_match_rate_pct": S["readback_match_rate"],
            "by_form_service_round_trip_median_ms": {v: round(st.median(r["t_service_ms"] for r in rs), 1) for v, rs in by.items()},
        }
    (D / "e2e_summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    md = ["# End-to-end software-path measurement with an emulated device", "",
          f"{out['host']}; {out['checkpoint']}; {out['threads']} threads; device: {out['device']}.", "",
          "| mode | n | service round trip median / p95 (ms) | inside service | emulated device | client total (admitted) | withheld | raw identical to evaluation | exact % |",
          "|---|--:|---|---|---|---|--:|--:|--:|"]
    for mode, m in out["modes"].items():
        md.append(f"| {mode} | {m['n_measured']} | {m['service_round_trip_ms']['median_ms']} / {m['service_round_trip_ms']['p95_ms']} | "
                  f"{m['service_internal_ms']['median_ms']} / {m['service_internal_ms']['p95_ms']} | {m['emulated_device_reply_ms']['median_ms']} / {m['emulated_device_reply_ms']['p95_ms']} | "
                  f"{m['client_total_ms_admitted_requests']['median_ms']} / {m['client_total_ms_admitted_requests']['p95_ms']} (n = {m['client_total_ms_admitted_requests']['n']}) | "
                  f"{m['withheld_by_gate']} / {m['rows']} | {m['raw_identical_to_stored_evaluation']} / {m['rows']} | {m['exact_vs_gold_pct_all_240']} |")
    md += ["", "Not included: the Wi-Fi hop to the bulb, the bulb firmware's response and the physical light transition."]
    (D / "e2e_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for mode, m in out["modes"].items():
        print(f"  {mode}: service {m['service_round_trip_ms']['median_ms']}/{m['service_round_trip_ms']['p95_ms']}  total {m['client_total_ms_admitted_requests']['median_ms']}/{m['client_total_ms_admitted_requests']['p95_ms']}  withheld {m['withheld_by_gate']}  identical {m['raw_identical_to_stored_evaluation']}/240")


if __name__ == "__main__":
    main()
