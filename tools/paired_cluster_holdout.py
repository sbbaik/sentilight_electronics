"""Paired frame-cluster bootstrap for the selected-minus-deployed difference on the unseen-frame hold-out.

Reviewer point (Electronics, round 2): the manuscript quotes a 5-seed paired t interval for the model difference
while stating that all hold-out intervals use the frame cluster bootstrap. The two answer different questions:
the t interval asks "on these fixed 32 frames, how does the difference move when the seed changes"; the cluster
interval asks "how does it move when the frames, or the frame families, could have been different ones".
This script computes the second for the difference itself, at both the frame and the family level.
"""
import json, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "Implement_New_Android_v6/backend/reports/holdout_final"
HOLDOUT = ROOT / "Implement_New_Android_v6/backend/models/compact_llm/datasets/holdout_natural/K240"
DIMS = ("H", "S", "B", "Dimmer", "CT")

FRAMES = json.loads((HOLDOUT / "frames.json").read_text(encoding="utf-8"))
FRAME_RE = []
for fam, lst in FRAMES.items():
    for i, f in enumerate(lst):
        pat = re.escape(f)
        for ph in ("\\{emotion\\}", "\\{modifier\\}", "\\{color\\}", "\\{text\\}"):
            pat = pat.replace(ph, "(?:.*?)")
        FRAME_RE.append((fam, f"{fam}#{i+1}", re.compile("^" + pat + "$")))
_c = {}
def frame_of(t):
    if t in _c: return _c[t]
    for fam, fid, rx in FRAME_RE:
        if rx.match(t): _c[t] = (fam, fid); return _c[t]
    _c[t] = ("unmatched", "unmatched"); return _c[t]

def key(o): return tuple(int(o[k]) for k in DIMS) if o else None

def load(cfg):
    out = {}
    for f in sorted((R / "per_row").glob(f"{cfg}_s*.jsonl")):
        m = re.match(rf"^{re.escape(cfg)}_s(\d+)$", f.stem)
        if not m: continue
        rows = [json.loads(l) for l in f.open(encoding="utf-8")]
        if len(rows) == 2000: out[int(m.group(1))] = rows
    return out

A_NAME, B_NAME = "selected_V4k_L8", "deployed_W384_L8_V24k"
A, B = load(A_NAME), load(B_NAME)
seeds = sorted(set(A) & set(B))
assert len(seeds) == 5, seeds

# align by row_index so the difference is genuinely paired per utterance
def indexed(rows): return {r["row_index"]: r for r in rows}
clusters = {}
for s in seeds:
    a, b = indexed(A[s]), indexed(B[s])
    common = sorted(set(a) & set(b))
    fam = defaultdict(lambda: defaultdict(list))
    for i in common:
        ra, rb = a[i], b[i]
        assert ra["input"] == rb["input"]
        ca = key(ra.get("predicted")) == key(ra["reference"])
        cb = key(rb.get("predicted")) == key(rb["reference"])
        fa, fi = frame_of(ra["input"])
        fam[fa][fi].append((ca, cb))
    clusters[s] = {fa: {fi: np.array(v, dtype=float) for fi, v in d.items()} for fa, d in fam.items()}

n_frames = len({fi for s in seeds for fa in clusters[s] for fi in clusters[s][fa]})
n_fams = len({fa for s in seeds for fa in clusters[s]})
print(f"seeds {len(seeds)}, frames {n_frames}, families {n_fams}")

def point():
    vals = []
    for s in seeds:
        pool = np.concatenate([clusters[s][fa][fi] for fa in clusters[s] for fi in clusters[s][fa]])
        vals.append(100 * (pool[:, 0].mean() - pool[:, 1].mean()))
    return st.mean(vals), vals

def boot(B_=4000, resample_families=False, alpha=(5, 95), seed=20260917):
    rng = np.random.default_rng(seed); out = []
    for _ in range(B_):
        ss = rng.choice(seeds, len(seeds), replace=True); vals = []
        for s in ss:
            fams = list(clusters[s])
            fd = rng.choice(fams, len(fams), replace=True) if resample_families else fams
            pool = []
            for fa in fd:
                frs = list(clusters[s][fa]); fr = rng.choice(frs, len(frs), replace=True)
                for fi in fr:
                    arr = clusters[s][fa][fi]
                    pool.append(arr[rng.integers(0, len(arr), len(arr))])
            p = np.concatenate(pool); vals.append(100 * (p[:, 0].mean() - p[:, 1].mean()))
        out.append(np.mean(vals))
    q = np.percentile(out, list(alpha))
    return float(np.mean(out)), float(q[0]), float(q[1])

mean, per_seed = point()
print(f"point difference {mean:+.2f} pp; per seed {[round(v,2) for v in per_seed]}")
res = {"point_pp": round(mean, 2), "per_seed_pp": [round(v, 2) for v in per_seed], "n_frames": n_frames, "n_families": n_fams}
for tag, fam_rs in (("frames_resampled", False), ("families_resampled", True)):
    for lvl, al in (("90", (5, 95)), ("95", (2.5, 97.5))):
        m, lo, hi = boot(resample_families=fam_rs, alpha=al)
        res[f"{tag}_ci{lvl}"] = [round(lo, 2), round(hi, 2)]
        print(f"  {tag} {lvl}% CI [{lo:+.2f}, {hi:+.2f}]  (boot mean {m:+.2f})")
(R / "paired_cluster_difference.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print("written", R / "paired_cluster_difference.json")
