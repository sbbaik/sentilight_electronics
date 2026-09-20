"""Decompose test errors of one or more runs by source layer and by policy attribute.

For each run (per_row jsonl) reports exact / coarse / strict pass rates split by
  source (combinations / conflict+adjective / fallback), presence of colour, emotion, intensity,
  and per colour, per emotion, per intensity value; plus which output dimension fails most.
Runs are pooled over seeds (each row counted once per seed) so numbers are seed-averaged rates.

Usage:
  python tools/decompose_errors.py --run C4kL4=backend/reports/scale_grid_combo/per_row/compactlm_C4kL4_f100_s{seed}.jsonl \
      --run V2V4k=backend/reports/scale_grid_vocab_natural/V4k/per_row/compactlm_V4k_f100_s{seed}.jsonl \
      --run W384=backend/reports/scale_grid_width/per_row/compactlm_W384_f100_s{seed}.jsonl --seeds 42 43 44 \
      --out backend/reports/scale_grid_combo/error_decomposition
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DIMS = ("H", "S", "B", "Dimmer", "CT")


def load(path: str, seeds: list[int]) -> list[dict]:
    rows = []
    for s in seeds:
        p = Path(path.format(seed=s))
        if not p.exists():
            continue
        for l in p.open(encoding="utf-8"):
            r = json.loads(l)
            pr, ref = r.get("predicted"), r["reference"]
            r["_exact"] = bool(pr) and all(int(pr[k]) == int(ref[k]) for k in DIMS)
            r["_seed"] = s
            rows.append(r)
    return rows


def rate(rows, key):
    return 100 * sum(1 for r in rows if r[key]) / len(rows) if rows else float("nan")


def group(rows, fn):
    g = defaultdict(list)
    for r in rows:
        g[fn(r)].append(r)
    return g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="NAME=path_template_with_{seed}")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    runs = {n: load(p, args.seeds) for n, p in (x.split("=", 1) for x in args.run)}
    names = list(runs)
    result = {}
    lines = ["# Error decomposition (rates in %, pooled over seeds)", "", f"- Runs: {', '.join(names)}; seeds {args.seeds}", ""]

    def section(title, fn, order=None):
        lines.extend([f"## {title}", "", "| group | n/seed | " + " | ".join(f"{n} exact / coarse" for n in names) + " |", "|---|--:|" + "--:|" * len(names)])
        groups = {n: group(runs[n], fn) for n in names}
        keys = order or sorted({k for g in groups.values() for k in g}, key=str)
        result[title] = {}
        for k in keys:
            cells = []
            for n in names:
                rs = groups[n].get(k, [])
                cells.append(f"{rate(rs, '_exact'):.1f} / {rate(rs, 'coarse'):.1f}" if rs else "·")
                result[title].setdefault(str(k), {})[n] = {"n": len(rs), "exact": rate(rs, "_exact"), "coarse": rate(rs, "coarse"), "strict": rate(rs, "strict")}
            n0 = len(groups[names[0]].get(k, [])) // max(1, len(args.seeds))
            lines.append(f"| {k} | {n0} | " + " | ".join(cells) + " |")
        lines.append("")

    section("By source layer", lambda r: r["source"], ["color_emotion_intensity_combinations", "conflict_and_color_adjective_cases", "ambiguous_fallback_cases"])
    section("By input structure", lambda r: ("colour" if r.get("base_color") else "no-colour") + " + " + ("emotion" if r.get("emotion") else "no-emotion") + (" + intensity" if (r.get("intensity") or "neutral") != "neutral" else ""))
    section("By colour", lambda r: r.get("base_color") or "(none)")
    section("By emotion", lambda r: r.get("emotion") or "(none)")
    section("By intensity", lambda r: r.get("intensity") or "neutral")

    # failing dimensions among coarse failures
    lines.extend(["## Most frequent failing dimension among coarse failures", "", "| run | " + " | ".join(DIMS) + " | coarse failures/seed |", "|---|" + "--:|" * (len(DIMS) + 1)])
    result["failing_dimensions"] = {}
    for n in names:
        c = Counter()
        fails = [r for r in runs[n] if not r["coarse"]]
        for r in fails:
            for d in r.get("coarse_mismatch_dimensions", []):
                c[d] += 1
        result["failing_dimensions"][n] = dict(c)
        lines.append(f"| {n} | " + " | ".join(str(c.get(d, 0)) for d in DIMS) + f" | {len(fails) / len(args.seeds):.0f} |")
    lines.append("")
    # exact-but-not-strict / strict-but-not-exact overlap, JSON errors
    lines.extend(["## Output validity", "", "| run | rows/seed | invalid or missing prediction (%) | exact ∧ ¬strict (%) | strict ∧ ¬exact (%) |", "|---|--:|--:|--:|--:|"])
    for n in names:
        rs = runs[n]; N = len(rs)
        inv = 100 * sum(1 for r in rs if not r.get("success", True) or not r.get("predicted")) / N
        a = 100 * sum(1 for r in rs if r["_exact"] and not r["strict"]) / N
        b = 100 * sum(1 for r in rs if r["strict"] and not r["_exact"]) / N
        result.setdefault("validity", {})[n] = {"invalid_pct": inv, "exact_not_strict_pct": a, "strict_not_exact_pct": b}
        lines.append(f"| {n} | {N // len(args.seeds)} | {inv:.2f} | {a:.2f} | {b:.2f} |")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
