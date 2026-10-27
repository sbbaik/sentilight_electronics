#!/usr/bin/env bash
# Software end-to-end measurement on one host: client -> FastAPI service (selected mixed-bit checkpoint, 4 threads)
# -> Tasmota emulator. No physical bulb, no network hop; see tasmota_emulator.py.
set -euo pipefail
W="$(cd "$(dirname "$0")/../.." && pwd)"; APP="${APP:-$HOME/Sentilight_Paper_2/Implement_New_Android_v6/backend}"
PY=/home/sbbaik/miniconda3/envs/sentilight/bin/python; OUT="$W/analysis/e2e_simulated"; mkdir -p "$OUT"
MODE="${MODE:-raw_text}"   # raw_text: the adapter hands the request to the model's own prompt builder (the evaluation condition);
                           # wrapper: the service's default COMPACTLM_JSON_PROMPT wrapper
sed "s/host: 0.0.0.0/host: 127.0.0.1/" "$W/tools/e2e/models.e2e_selected.yaml" > "$OUT/models.e2e_loopback.yaml"
[[ "$MODE" == wrapper ]] && sed -i "/input_mode: raw_text/d" "$OUT/models.e2e_loopback.yaml"
"$PY" "$W/tools/e2e/tasmota_emulator.py" --port 8081 > "$OUT/emulator.log" 2>&1 & EM=$!
( cd "$APP" && OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 SENTILIGHT_MODELS_CONFIG="$OUT/models.e2e_loopback.yaml" SENTILIGHT_EAGER_LOAD=1 \
  exec "$PY" -m server.main > "$OUT/service.log" 2>&1 ) & SP=$!
trap 'kill $SP $EM 2>/dev/null || true' EXIT
for i in $(seq 1 90); do sleep 1; curl -s -m 2 http://127.0.0.1:8100/health > /dev/null 2>&1 && break; done
curl -s -m 5 http://127.0.0.1:8100/models > "$OUT/service_models.json"; cat "$OUT/service_models.json"; echo
date '+%F %T %Z' > "$OUT/measured_at_$MODE.txt"
"$PY" "$W/tools/e2e/measure_e2e_latency.py" --server http://127.0.0.1:8100 --model compact_llm_q4 --bulb 127.0.0.1:8081 \
  --dataset "$W/data/audited_requests/audited_requests_K240.jsonl" --form all --n 235 --warmup 5 --readback --pause 0.2 \
  --out "$OUT/e2e_emulated_bulb_$MODE.jsonl" > "$OUT/measure.log" 2>&1
tail -28 "$OUT/measure.log"
