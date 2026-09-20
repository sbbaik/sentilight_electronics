"""Run the deployed catalogue gate over the stored per-row outputs of the three evaluation sets.

This is not a re-analysis of the model. It replays what `common.policy_catalogue` — the gate now sitting in the
service's prediction path — would have done to each recorded prediction, so the manuscript can report the gate's
operating behaviour rather than a property observed after the fact. Reported per set, over the five seeds:

  rejected %        share of requests the gate withholds
  false rejections  requests the gate withholds although the tuple equalled the policy gold (must be zero)
  errors caught %   share of wrong requests the gate withholds
  errors missed %   share of all requests answered wrongly that the gate still lets through
"""
import json, statistics as st, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from common.lighting_schema import LightingValues          # noqa: E402
from common.policy_catalogue import get_catalogue          # noqa: E402

R = ROOT / "backend/reports"
SETS = {
    "development test":  (R / "scale_grid_vocab_natural/V4k/per_row", "compactlm_V4k_f100"),
    "unseen-frame hold-out": (R / "holdout_final/per_row", "selected_V4k_L8"),
    "machine-paraphrase stress set": (R / "holdout_paraphrase/per_row", "selected_V4k_L8"),
}
DIMS = ("H", "S", "B", "Dimmer", "CT")
cat = get_catalogue()
print(f"gate catalogue: {len(cat)} tuples, sha256 {cat.sha256[:16]}\n")


def key(o):
    return tuple(int(o[d]) for d in DIMS) if o else None


out = {"catalogue": {"count": len(cat), "sha256": cat.sha256}, "sets": {}}
for label, (d, stem) in SETS.items():
    files = sorted(p for p in d.glob(f"{stem}_s*.jsonl") if "_mixed4_" not in p.name)
    if not files:
        print(f"[skip] {label}: no per-row files under {d}"); continue
    rej, fr, caught, missed, n = [], 0, [], [], []
    for f in files:
        rows = [json.loads(l) for l in f.open(encoding="utf-8")]
        r_rej = r_wrong = r_caught = 0
        for row in rows:
            pred, gold = row.get("predicted"), row["reference"]
            correct = key(pred) == key(gold)
            if pred is None:
                blocked = True                       # unparseable output never reaches the device
            else:
                blocked = cat.gate(LightingValues(**{k: int(pred[k]) for k in DIMS}), "reject").executed is None
            r_rej += blocked
            r_wrong += (not correct)
            r_caught += (blocked and not correct)
            if blocked and correct:
                fr += 1
        n.append(len(rows))
        rej.append(100 * r_rej / len(rows))
        caught.append(100 * r_caught / r_wrong if r_wrong else float("nan"))
        missed.append(100 * (r_wrong - r_caught) / len(rows))

    def ms(x):
        return (st.mean(x), st.stdev(x) if len(x) > 1 else 0.0)
    (rm, rs), (cm, cs), (mm, ms_) = ms(rej), ms(caught), ms(missed)
    out["sets"][label] = {"seeds": len(files), "rows_per_seed": n[0],
                          "rejected_pct": [round(rm, 2), round(rs, 2)],
                          "false_rejections": fr,
                          "errors_caught_pct": [round(cm, 2), round(cs, 2)],
                          "errors_missed_pct_of_all_rows": [round(mm, 2), round(ms_, 2)]}
    print(f"{label} ({len(files)} seeds x {n[0]} rows)")
    print(f"  rejected        {rm:5.2f} ± {rs:.2f} %")
    print(f"  false rejections {fr}")
    print(f"  errors caught   {cm:5.2f} ± {cs:.2f} % of wrong rows")
    print(f"  errors missed   {mm:5.2f} ± {ms_:.2f} % of all rows\n")

dest = R / "policy_gate_measurement.json"
dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("written", dest)
