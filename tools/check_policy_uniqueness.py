"""Enumerate every nested K_eff policy in config/keff_policies.json and verify
that the reachable action set is exactly as large as intended.

Checks per policy
  1. reachable tuples == (C+1)(E+1)I  (no collisions after normalisation)
  2. the 18-degree hue snap never fires (same property as the production policy)
  3. nesting: each policy's reachable set is a superset of the smaller policy
  4. K240 reproduces training_data.resolve_case_output() tuple-for-tuple
  5. separability diagnostics: minimum pairwise distance, and the number of
     tuple pairs that fall inside the strict tolerance box (H20/S20/B20/D20/CT80)
     -- pairs the strict metric cannot tell apart.

Usage:  python tools/check_policy_uniqueness.py [--config config/keff_policies.json]
                                                 [--report-dir backend/reports/keff_policies]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "backend" / "models"))

from common.lighting_spec import (  # noqa: E402
    HUE_ANCHOR_SNAP_DEGREES,
    STRICT_TOLERANCES,
    hue_distance,
)
from compact_llm import training_data as td  # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")
RANGES = {"H": 360.0, "S": 100.0, "B": 100.0, "Dimmer": 100.0, "CT": 347.0}  # 153..500


def tup(o: dict) -> tuple[int, int, int, int, int]:
    return tuple(int(o[k]) for k in DIMS)


def resolve(cat: dict, fallback: dict, color: str | None, emotion: str | None, intensity: str) -> tuple[dict, bool]:
    """Same composition as training_data.resolve_case_output, parameterised by catalog."""
    inten = cat["intensities"][intensity]["adjust"]
    snapped = False
    if color:
        c = cat["colors"][color]
        emo_adj = cat["emotions"][emotion]["adjust"] if emotion else None
        out = td.apply_adjustments(dict(c["target"]), emo_adj, inten)
        if hue_distance(out["H"], c["anchor_h"]) > HUE_ANCHOR_SNAP_DEGREES:
            out["H"] = c["anchor_h"]
            snapped = True
        return out, snapped
    if emotion:
        return td.apply_adjustments(dict(cat["emotions"][emotion]["target"]), inten), False
    return td.apply_adjustments(dict(fallback), inten), False


def norm_dist(a, b) -> float:
    d2 = (hue_distance(a[0], b[0]) / 180.0) ** 2
    for i, k in enumerate(DIMS[1:], start=1):
        d2 += ((a[i] - b[i]) / RANGES[k]) ** 2
    return d2 ** 0.5


def within_strict(a, b) -> bool:
    if hue_distance(a[0], b[0]) > STRICT_TOLERANCES["H"]:
        return False
    return all(abs(a[i] - b[i]) <= STRICT_TOLERANCES[k] for i, k in enumerate(DIMS[1:], start=1))


def enumerate_policy(cat: dict, fallback: dict, pol: dict) -> dict:
    colors = [None] + list(pol["colors"])
    emotions = [None] + list(pol["emotions"])
    intensities = list(pol["intensities"])
    seen: dict[tuple, list[tuple]] = {}
    snaps = 0
    max_drift = 0
    for c in colors:
        for e in emotions:
            for i in intensities:
                out, snapped = resolve(cat, fallback, c, e, i)
                snaps += snapped
                if c:
                    dh = (cat["emotions"][e]["adjust"]["H"] if e else 0) + cat["intensities"][i]["adjust"]["H"]
                    max_drift = max(max_drift, abs(dh))
                seen.setdefault(tup(out), []).append((c, e, i))
    lattice = len(colors) * len(emotions) * len(intensities)
    collisions = {str(k): v for k, v in seen.items() if len(v) > 1}
    tuples = sorted(seen)
    # separability
    min_d, min_pair = 9.0, None
    strict_conf = 0
    for a, b in itertools.combinations(tuples, 2):
        d = norm_dist(a, b)
        if d < min_d:
            min_d, min_pair = d, (seen[a][0], seen[b][0], a, b)
        if within_strict(a, b):
            strict_conf += 1
    return {
        "lattice": lattice,
        "reachable": len(tuples),
        "k_eff_target": pol["k_eff_target"],
        "ok_size": len(tuples) == lattice == pol["k_eff_target"],
        "collisions": collisions,
        "hue_snaps": snaps,
        "max_hue_drift_deg": max_drift,
        "min_pairwise_norm_distance": round(min_d, 4),
        "closest_pair": {"a": min_pair[0], "b": min_pair[1], "tuple_a": min_pair[2], "tuple_b": min_pair[3]} if min_pair else None,
        "pairs_within_strict_box": strict_conf,
        "pairs_total": len(tuples) * (len(tuples) - 1) // 2,
        "tuples": [list(t) for t in tuples],
        "tuple_to_case": {str(list(k)): v[0] for k, v in seen.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "keff_policies.json")
    ap.add_argument("--report-dir", type=Path, default=REPO_ROOT / "backend" / "reports" / "keff_policies")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cat, fallback = cfg["catalog"], cfg["safe_fallback"]

    # sanity: production items in the catalog must equal training_data.py
    drift = []
    for name, c in td.COLOR_PROFILES.items():
        k = cat["colors"][name]
        if k["anchor_h"] != c["anchor_h"] or k["target"] != c["target"]:
            drift.append(f"color {name}")
    for name, e in td.EMOTION_PROFILES.items():
        k = cat["emotions"][name]
        if k["target"] != e["target"] or k["adjust"] != e["adjust"]:
            drift.append(f"emotion {name}")
    for name, i in td.INTENSITY_MODIFIERS.items():
        if cat["intensities"][name]["adjust"] != i["adjust"]:
            drift.append(f"intensity {name}")
    if fallback != td.SAFE_FALLBACK:
        drift.append("safe_fallback")

    results = {}
    order = sorted(cfg["policies"], key=lambda n: cfg["policies"][n]["k_eff_target"])
    for name in order:
        results[name] = enumerate_policy(cat, fallback, cfg["policies"][name])

    # nesting
    nesting = {}
    chain = [n for n in order if not cfg["policies"][n].get("control")]  # control policies are not part of the nested chain
    for small, big in zip(chain, chain[1:]):
        s, b = set(map(tuple, results[small]["tuples"])), set(map(tuple, results[big]["tuples"]))
        nesting[f"{small} ⊂ {big}"] = s <= b

    # K240 must reproduce production resolve_case_output exactly
    prod = set()
    for c in [None] + list(td.COLOR_PROFILES):
        for e in [None] + list(td.EMOTION_PROFILES):
            for i in td.INTENSITY_MODIFIERS:
                prod.add(tup(td.normalize_output(td.resolve_case_output({"base_color": c, "emotion": e, "intensity": i}))))
    k240_ok = prod == set(map(tuple, results["K240"]["tuples"])) if "K240" in results else None

    all_ok = not drift and all(r["ok_size"] and r["hue_snaps"] == 0 for r in results.values()) and all(nesting.values()) and bool(k240_ok)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "keff_policy_check.json").write_text(
        json.dumps({"config": str(args.config), "catalog_drift_vs_training_data": drift, "policies": results, "nesting": nesting,
                    "k240_equals_production": k240_ok, "all_ok": all_ok}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    lines = ["# K_eff policy uniqueness check", "", f"- Config: `{args.config.relative_to(REPO_ROOT)}`",
             f"- Catalog drift vs training_data.py: {drift or 'none'}",
             f"- K240 reproduces production resolve_case_output: {k240_ok}", ""]
    lines += ["| Policy | C | E | I | Lattice | Reachable | Target | Collisions | Hue snaps | Max ΔH | Min pair dist | Pairs inside strict box |",
              "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for name in order:
        p, r = cfg["policies"][name], results[name]
        lines.append(f"| {name} | {len(p['colors'])} | {len(p['emotions'])} | {len(p['intensities'])} | {r['lattice']} | {r['reachable']} | {r['k_eff_target']} | "
                     f"{len(r['collisions'])} | {r['hue_snaps']} | {r['max_hue_drift_deg']}° | {r['min_pairwise_norm_distance']} | "
                     f"{r['pairs_within_strict_box']} / {r['pairs_total']} |")
    lines += ["", "## Nesting"] + [f"- {k}: {v}" for k, v in nesting.items()]
    lines += ["", "## Closest pair per policy"]
    for name in order:
        cp = results[name]["closest_pair"]
        lines.append(f"- {name}: {cp['a']} {cp['tuple_a']}  vs  {cp['b']} {cp['tuple_b']}")
    for name in order:
        if results[name]["collisions"]:
            lines += ["", f"## Collisions in {name}"] + [f"- {k}: {v}" for k, v in results[name]["collisions"].items()]
    lines += ["", f"**ALL OK: {all_ok}**"]
    (args.report_dir / "keff_policy_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
