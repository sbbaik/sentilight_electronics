"""A2K192 L = 2 seeds 45/46: failure-signature analysis (not a mechanism test).
Per seed: JSON/parse errors, distinct in-policy vs out-of-policy predicted tuples, out-of-policy row rate, top-5 share;
exact rate by colour / emotion / input source with n; Wilson 95% CIs and per-dimension mismatch for selected emotions.
Output: backend/reports/scale_grid_depth_a2/D2_seed_instability.{md,json}"""
import json, collections, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "backend" / "reports" / "scale_grid_depth_a2"
DIMS = ("H", "S", "B", "Dimmer", "CT"); SEEDS = [42, 43, 44, 45, 46]
REACH = {tuple(t) for t in json.load(open(ROOT / "backend/reports/keff_policies/keff_policy_check.json"))["policies"]["A2K192"]["tuples"]}
def load(sc, s): return [json.loads(l) for l in (R / "per_row" / f"compactlm_{sc}_f100_s{s}.jsonl").open(encoding="utf-8")]
def tup(o): return tuple(int(o[k]) for k in DIMS)
def exact(r): return bool(r.get("predicted")) and tup(r["predicted"]) == tup(r["reference"])
def rate(rows): return 100 * sum(exact(r) for r in rows) / len(rows) if rows else float("nan")
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return 100 * (c - h), 100 * (c + h)
out, L = {"reachable_tuples": len(REACH)}, ["# A2K192 L = 2: seed-instability failure signature", "",
    f"Policy A2K192 has {len(REACH)} reachable tuples; the 2,000-row test covers all of them. Seeds 45/46 trained normally (validation loss at or below the other seeds). "
    "This analysis identifies a failure signature; it does not establish a causal mechanism.", ""]
for sc in ("D2", "D4"):
    rows = {s: load(sc, s) for s in SEEDS}; out[sc] = {"concentration": {}}
    L += [f"## {sc}: output validity and concentration", "", "| seed | exact % | JSON/parse errors | distinct in-policy tuples (of 192) | distinct out-of-policy tuples | out-of-policy rows % | top-5 predicted share % |", "|--:|--:|--:|--:|--:|--:|--:|"]
    for s in SEEDS:
        preds = [tup(r["predicted"]) for r in rows[s] if r.get("predicted")]; err = len(rows[s]) - len(preds) + sum(1 for r in rows[s] if r.get("error"))
        c = collections.Counter(preds); inp = sum(1 for p in c if p in REACH); outp = len(c) - inp; outrows = 100 * sum(v for p, v in c.items() if p not in REACH) / len(preds)
        top5 = 100 * sum(v for _, v in c.most_common(5)) / len(preds)
        out[sc]["concentration"][s] = {"exact": rate(rows[s]), "errors": err, "distinct_in_policy": inp, "distinct_out_of_policy": outp, "out_of_policy_rows_pct": outrows, "top5_share_pct": top5}
        L.append(f"| {s} | {rate(rows[s]):.1f} | {err} | {inp} | {outp} | {outrows:.1f} | {top5:.1f} |")
    L.append("")
    for field in ("emotion", "base_color", "source"):
        vals = sorted({r.get(field) or "none" for r in rows[42]}); out[sc][field] = {}
        L += [f"## {sc}: exact % by {field} (n = rows per category)", "", f"| {field} | n | " + " | ".join(f"s{s}" for s in SEEDS) + " |", "|---|--:|" + "--:|" * len(SEEDS)]
        for v in vals:
            per = {s: rate([r for r in rows[s] if (r.get(field) or "none") == v]) for s in SEEDS}; n = sum(1 for r in rows[42] if (r.get(field) or "none") == v)
            out[sc][field][v] = {"n": n, **{str(s): per[s] for s in SEEDS}}; L.append(f"| {v} | {n} | " + " | ".join(f"{per[s]:.1f}" for s in SEEDS) + " |")
        L.append("")
rows = {s: load("D2", s) for s in SEEDS}; out["D2_emotion_detail"] = {}
L += ["## D2: selected emotions — exact % with Wilson 95% CI and per-dimension mismatch % among those rows", "", "| emotion | seed | n | exact % [95% CI] | mismatch H / S / B / Dimmer / CT % |", "|---|--:|--:|---|---|"]
for emo in ("anger", "boredom", "calm", "fatigue", "surprise"):
    for s in SEEDS:
        rr = [r for r in rows[s] if r.get("emotion") == emo and r.get("predicted")]; k = sum(exact(r) for r in rr); lo, hi = wilson(k, len(rr))
        mism = [100 * sum(1 for r in rr if int(r["predicted"][d]) != int(r["reference"][d])) / len(rr) for d in DIMS]
        out["D2_emotion_detail"][f"{emo}_s{s}"] = {"n": len(rr), "exact": 100 * k / len(rr), "ci95": [lo, hi], "mismatch": dict(zip(DIMS, mism))}
        L.append(f"| {emo} | {s} | {len(rr)} | {100*k/len(rr):.1f} [{lo:.1f}, {hi:.1f}] | " + " / ".join(f"{m:.0f}" for m in mism) + " |")
L += ["", "## Reading", "",
      "- No output-mode collapse: seeds 45/46 predict 179 and 158 distinct in-policy tuples (others 180–185), top-5 share 9–11 % (others 6–9 %), zero JSON errors. Out-of-policy outputs rise only modestly (1.7 % and 4.2 % of rows vs 1.4–2.0 %). Seed 46 does, however, fail to produce 34 of the 192 policy tuples.",
      "- Errors concentrate in particular emotions: anger and boredom fall to 45/48 % (seed 45) and 13/13 % (seed 46) against 69–90 % at seeds 42–44 (n = 168–169 per emotion, Wilson CIs non-overlapping), while fatigue and surprise stay at 86–96 %. Within the failing rows all five dimensions are wrong together (mismatch 52–55 % / 82–87 % on every dimension), i.e. the model emits a different whole tuple rather than mis-scaling one attribute.",
      "- At L = 4 the same seeds recover these emotions (anger 67.9 / 93.5 %, boredom 63.9 / 75.7 %) and in-policy coverage returns to 189–190 tuples.",
      "- Interpretation: the error concentration in anger and boredom, together with recovery at L = 4, suggests seed-sensitive difficulty in learning the policy's emotion-conditioned tuples at L = 2. This is a failure signature, not an established mechanism; the earlier statement that failures were specific to the S/B dimensions is withdrawn (mismatch is uniform across dimensions within failing rows)."]
(R / "D2_seed_instability.md").write_text("\n".join(L) + "\n", encoding="utf-8"); (R / "D2_seed_instability.json").write_text(json.dumps(out, indent=1), encoding="utf-8"); print("written")
