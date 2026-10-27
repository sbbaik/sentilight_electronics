# -*- coding: utf-8 -*-
"""A minimal Tasmota HTTP emulator standing in for a bulb that the measuring host cannot reach.

It answers the same URL the SentiLight client sends, `GET /cm?cmnd=Backlog0 HSBCOLOR h,s,b;Dimmer d;CT ct`,
parses the command, keeps the resulting state and replies with a Tasmota-shaped JSON body. `cm?cmnd=State`
returns the state. It adds NO artificial delay: what it measures is the client's HTTP round trip to a device
endpoint on the same host, not a bulb's firmware or a Wi-Fi hop. Say so wherever its numbers are reported.

Usage: python tasmota_emulator.py --host 127.0.0.1 --port 8081
"""
from __future__ import annotations

import argparse
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

STATE = {"POWER": "ON", "Dimmer": 50, "HSBColor": "0,0,50", "CT": 326}
LOCK = threading.Lock()
LOG = []


def apply(cmd: str) -> dict:
    """Execute a Backlog of HSBCOLOR / Dimmer / CT commands; return the Tasmota-style reply of the backlog."""
    parts = [p.strip() for p in re.sub(r"^Backlog0?\s+", "", cmd.strip(), flags=re.I).split(";") if p.strip()]
    reply = {}
    with LOCK:
        for p in parts:
            m = re.match(r"(?i)(HSBCOLOR|Dimmer|CT)\s+(.+)", p)
            if not m:
                continue
            k, v = m.group(1).upper(), m.group(2).strip()
            if k == "HSBCOLOR":
                h, s, b = (int(float(x)) for x in v.split(","))
                STATE["HSBColor"] = f"{h},{s},{b}"; STATE["Dimmer"] = b
            elif k == "DIMMER":
                STATE["Dimmer"] = int(float(v))
            elif k == "CT":
                STATE["CT"] = int(float(v))
            STATE["POWER"] = "ON"
        reply.update({"POWER": STATE["POWER"], "Dimmer": STATE["Dimmer"], "HSBColor": STATE["HSBColor"], "CT": STATE["CT"]})
    return reply


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):          # quiet
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/cm":
            self.send_response(404); self.end_headers(); return
        cmd = unquote(parse_qs(u.query).get("cmnd", [""])[0])
        if cmd.strip().lower() == "state":
            with LOCK:
                body = dict(STATE)
        else:
            body = apply(cmd)
        LOG.append(cmd)
        data = json.dumps(body).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=8081)
    A = ap.parse_args()
    srv = ThreadingHTTPServer((A.host, A.port), H)
    print(f"tasmota emulator on http://{A.host}:{A.port}/cm  (no artificial delay)", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
