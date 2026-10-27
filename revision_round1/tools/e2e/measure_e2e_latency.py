# -*- coding: utf-8 -*-
"""End-to-end latency of the SentiLight request path: client -> model service -> Tasmota bulb.

Run this ON A MACHINE THAT REACHES THE BULBS (the laboratory LAN, 192.168.0.x) while the model service runs on
the workstation (tools/e2e/models.e2e_selected.yaml, reachable over Tailscale at http://100.73.212.124:8100).
Needs Python 3.9+ and the `requests` package only (pip install requests).

What is timed, per request, with time.perf_counter():
  t_service  POST /predict/<model>   text in, gated five-field tuple out   (network + inference + gate)
  t_bulb     GET  http://<bulb>/cm?cmnd=Backlog0 HSBCOLOR h,s,b;Dimmer d;CT ct   until the bulb's HTTP reply
  t_total    from before the POST to after the bulb's reply, i.e. what the Android client would wait
Optionally (--readback) the bulb state is read back with `cm?cmnd=State` and compared with the command; this is
a separate request and is not included in t_total.

The text set is the first N plain requests of the audited request set (gold tuple included), so the service
answers can also be compared with the stored evaluation output of the same checkpoint.

Example (Windows PowerShell or any shell):
  python measure_e2e_latency.py --server http://100.73.212.124:8100 --model compact_llm_q4 --bulb 192.168.0.105 ^
      --dataset audited_requests_K240.jsonl --n 50 --warmup 5 --readback --out e2e_latency.jsonl
Dry run without touching a bulb:  add --dry-run  (bulb stage is skipped, t_bulb = null).
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics as st
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

DIMS = ("H", "S", "B", "Dimmer", "CT")
LIMITS = {"H": (0, 360), "S": (0, 100), "B": (0, 100), "Dimmer": (0, 100), "CT": (153, 500)}


def clamp(v, lo, hi):
    try:
        v = int(round(float(v)))
    except (TypeError, ValueError):
        v = lo
    return max(lo, min(hi, v))


def tasmota_command(lighting: dict) -> str:
    """Identical to frontend/common/tasmota_controller.py: Backlog0 HSBCOLOR H,S,B;Dimmer D;CT CT."""
    v = {k: clamp(lighting.get(k), *LIMITS[k]) for k in DIMS}
    return f"Backlog0 HSBCOLOR {v['H']},{v['S']},{v['B']};Dimmer {v['Dimmer']};CT {v['CT']}"


def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summary(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    return {"n": len(xs), "median_ms": round(st.median(xs), 1), "p95_ms": round(pct(xs, 0.95), 1),
            "mean_ms": round(st.mean(xs), 1), "min_ms": round(min(xs), 1), "max_ms": round(max(xs), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True); ap.add_argument("--model", default="compact_llm_q4")
    ap.add_argument("--bulb", default=None, help="bulb IP on the LAN, e.g. 192.168.0.105")
    ap.add_argument("--dataset", required=True, help="audited_requests_K240.jsonl")
    ap.add_argument("--n", type=int, default=50); ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--form", default="plain", help="request form to use: plain|negation|word_order|context_clause|all")
    ap.add_argument("--readback", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0); ap.add_argument("--out", default="e2e_latency.jsonl")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    A = ap.parse_args()
    if not A.dry_run and not A.bulb:
        sys.exit("--bulb is required unless --dry-run")

    rows = [json.loads(l) for l in open(A.dataset, encoding="utf-8")]
    if A.form != "all":
        rows = [r for r in rows if r.get("source", "").endswith(A.form) or r.get("variation") == A.form]
    rows = rows[: A.warmup + A.n]
    print(f"server {A.server}  model {A.model}  bulb {A.bulb or '(dry run)'}  rows {len(rows)} (warm-up {A.warmup})")
    health = requests.get(f"{A.server}/health", timeout=A.timeout).json()
    print("service health:", json.dumps(health)[:200])

    recs = []
    with open(A.out, "w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            rec = {"i": i, "warmup": i < A.warmup, "input": r["input"], "gold": r.get("output"),
                   "cell_id": r.get("cell_id"), "variation": r.get("variation")}
            t0 = time.perf_counter()
            try:
                resp = requests.post(f"{A.server}/predict/{A.model}", json={"text": r["input"]}, timeout=A.timeout)
                t1 = time.perf_counter(); body = resp.json()
                rec.update({"service_http": resp.status_code, "service_ok": bool(body.get("success")),
                            "lighting": body.get("lighting"), "raw": body.get("raw"),
                            "gate_in_policy": (body.get("policy_gate") or {}).get("in_policy"),
                            "service_internal_latency_ms": body.get("latency_ms"),
                            "service_error": body.get("error"), "t_service_ms": round((t1 - t0) * 1000, 2)})
            except Exception as exc:                                   # noqa: BLE001
                t1 = time.perf_counter()
                rec.update({"service_ok": False, "service_error": str(exc), "t_service_ms": round((t1 - t0) * 1000, 2), "lighting": None})
            lighting = rec.get("lighting")
            rec["exact_vs_gold"] = bool(lighting and rec["gold"] and all(int(lighting[d]) == int(rec["gold"][d]) for d in DIMS))
            if lighting and not A.dry_run:
                cmd = tasmota_command(lighting); url = f"http://{A.bulb}/cm?cmnd={quote(cmd, safe='')}"
                t2 = time.perf_counter()
                try:
                    b = requests.get(url, timeout=A.timeout); t3 = time.perf_counter()
                    rec.update({"command": cmd, "bulb_http": b.status_code, "bulb_ok": b.ok, "bulb_reply": b.text[:300],
                                "t_bulb_ms": round((t3 - t2) * 1000, 2), "t_total_ms": round((t3 - t0) * 1000, 2)})
                except Exception as exc:                               # noqa: BLE001
                    t3 = time.perf_counter()
                    rec.update({"command": cmd, "bulb_ok": False, "bulb_error": str(exc), "t_bulb_ms": round((t3 - t2) * 1000, 2), "t_total_ms": None})
                if A.readback:
                    try:
                        s = requests.get(f"http://{A.bulb}/cm?cmnd=State", timeout=A.timeout).json()
                        rec["readback"] = {k: s.get(k) for k in ("HSBColor", "Dimmer", "CT")}
                        v = {k: clamp(lighting.get(k), *LIMITS[k]) for k in DIMS}
                        rec["readback_matches"] = (s.get("HSBColor") == f"{v['H']},{v['S']},{v['B']}" and s.get("Dimmer") == v["Dimmer"] and s.get("CT") == v["CT"])
                    except Exception as exc:                           # noqa: BLE001
                        rec["readback_error"] = str(exc)
            else:
                rec.update({"t_bulb_ms": None, "t_total_ms": None if not A.dry_run else rec.get("t_service_ms")})
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); recs.append(rec)
            print(f"{i:3d} {'w' if rec['warmup'] else ' '} service {rec.get('t_service_ms')} ms  bulb {rec.get('t_bulb_ms')} ms  total {rec.get('t_total_ms')} ms  "
                  f"{'exact' if rec['exact_vs_gold'] else 'wrong'}  {'' if rec.get('bulb_ok', True) else 'BULB FAIL'}")
            time.sleep(A.pause)

    meas = [r for r in recs if not r["warmup"]]
    out = {"measured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "client": platform.platform(),
           "python": platform.python_version(), "server": A.server, "model": A.model, "bulb": A.bulb, "dry_run": A.dry_run,
           "form": A.form, "n": len(meas), "warmup": A.warmup, "readback": A.readback,
           "t_service_ms": summary([r.get("t_service_ms") for r in meas]),
           "service_internal_latency_ms": summary([r.get("service_internal_latency_ms") for r in meas]),
           "t_bulb_ms": summary([r.get("t_bulb_ms") for r in meas]), "t_total_ms": summary([r.get("t_total_ms") for r in meas]),
           "service_ok_rate": round(100 * st.mean(bool(r.get("service_ok")) for r in meas), 1) if meas else None,
           "bulb_ok_rate": round(100 * st.mean(bool(r.get("bulb_ok")) for r in meas if "bulb_ok" in r), 1) if any("bulb_ok" in r for r in meas) else None,
           "exact_vs_gold_pct": round(100 * st.mean(r["exact_vs_gold"] for r in meas), 1) if meas else None,
           "readback_match_rate": round(100 * st.mean(bool(r.get("readback_matches")) for r in meas if "readback" in r), 1) if any("readback" in r for r in meas) else None}
    with open(A.out.replace(".jsonl", "_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
