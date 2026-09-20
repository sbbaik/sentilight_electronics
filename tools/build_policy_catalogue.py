"""Enumerate the executable action set once and freeze it for the service to load.

The service must not import the training package to answer a request, so the catalogue is materialised here and
read back as data. Enumeration follows Algorithm 1 of the manuscript exactly: every admissible (colour, emotion,
intensity) combination is resolved through the policy and the device map, the resulting five-value tuples are
normalised, and duplicates are merged. The SHA-256 of the sorted tuple list is recorded so that the service can
assert at start-up that it is gating against the same catalogue the paper reports.
"""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend/models/compact_llm"))
import training_data as td  # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")
tuples, provenance = set(), {}
for colour in [None] + list(td.COLOR_PROFILES):
    for emotion in [None] + list(td.EMOTION_PROFILES):
        for intensity in td.INTENSITY_MODIFIERS:
            out = td.normalize_output(td.resolve_case_output(
                {"base_color": colour, "emotion": emotion, "intensity": intensity}))
            key = tuple(int(out[d]) for d in DIMS)
            tuples.add(key)
            provenance.setdefault(key, []).append([colour, emotion, intensity])

rows = sorted(tuples)
digest = hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()
collisions = sum(1 for k in rows if len(provenance[k]) > 1)
doc = {
 "policy": "K240 (production)",
 "dimensions": list(DIMS),
 "count": len(rows),
 "sha256": digest,
 "collisions_merged": collisions,
 "enumerated_combinations": sum(len(v) for v in provenance.values()),
 "tuples": [list(r) for r in rows],
}
dest = ROOT / "backend/config/policy_catalogue_k240.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(doc, indent=1), encoding="utf-8")
print(f"{len(rows)} tuples from {doc['enumerated_combinations']} combinations, "
      f"{collisions} merged; sha256 {digest[:16]}")
print("written", dest)
