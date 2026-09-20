"""Build policy-only SFT train/val splits and a rule test set for every nested
K_eff policy in config/keff_policies.json (K48, K240, K480, K960).

Design
  * Training rows come from the PRODUCTION generator
    (compact_llm.training_data.build_synthetic_rows) executed with the module's
    profile tables swapped for the policy's catalogue subset. Templates, phrase
    caps, the 90/10 split (seed 42) and the per-source repeat factors are the
    ones prepare_datasets() uses, so K240 reproduces the production
    policy-only rows and larger policies differ only in the catalogue.
  * Natural-language (teacher-labelled) rows are NOT included: their tuples
    lie outside every policy and would be constant noise across K_eff. Pass
    --include-natural to append the 36,000 base_train rows for parity with the
    W-series train_100 mixture.
  * Test rows reuse the v3 benchmark templates (holdout combinations, colour-
    adjective / conflict hard cases, ambiguous fallback), deduplicated against
    train+val on (input, emotion, base_color, intensity). Sampling first takes
    --min-per-tuple rows for every reachable tuple, then fills the remaining
    budget by source in the production 70/20/10 proportion. Every reachable
    tuple is therefore covered (the production rule-1000 set covered 219/240).

Outputs per policy under --out-root/<policy>/:
  train_100.jsonl  val.jsonl  test_rule.jsonl  policy.json  manifest.json
plus <out-root>/keff_series_manifest.json.

Usage: python tools/build_keff_datasets.py [--policies K48 K240 K480 K960]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "backend" / "models"))

from compact_llm import training_data as td  # noqa: E402

DIMS = ("H", "S", "B", "Dimmer", "CT")
KeyT = tuple[str, str | None, str | None, str | None]

# ---- v3 benchmark templates (verbatim copies of scripts/create_v3_benchmark_dataset.py) ----
HOLDOUT_MIXED = [
    "내 기분은 {emotion} 쪽이고, 전등은 {modifier}{color} 분위기로 맞춰줘",
    "{emotion}한 마음이야. 빛은 {modifier}{color} 계열로 정돈해줘",
    "오늘 감정은 {emotion}에 가까워. 그래도 조명 색은 {modifier}{color}으로 부탁해",
    "{emotion} 느낌이 올라오는데, 방은 {modifier}{color}빛으로 채워줘",
]
HOLDOUT_COLOR_ONLY = [
    "감정보다는 색이 중요해. {modifier}{color} 톤으로 설정해줘",
    "지금은 {modifier}{color} 조명이 제일 어울려",
    "{modifier}{color} 계열로 방 분위기를 잡아줘",
]
HOLDOUT_EMOTION_ONLY = [
    "색 지정은 없어. 지금 감정은 {emotion} 쪽이야",
    "{emotion}한 상태라서 그 감정에 맞는 빛으로 해줘",
    "조명 색은 맡길게. 나는 지금 {emotion} 느낌이야",
]
# Production templates above carry no intensity word, yet the v3 benchmark emitted them once per
# intensity with different gold tuples (34 inputs / 105 rows of rule-1000 are unanswerable).
# For non-neutral intensity the K-series uses templates that name the intensity.
HOLDOUT_EMOTION_ONLY_INTENSITY = [
    "색 지정은 없어. 지금 감정은 {emotion} 쪽이야. 빛은 {modifier}느낌으로",
    "{emotion}한 상태라서 그 감정에 맞는 {modifier}빛으로 해줘",
    "조명 색은 맡길게. 나는 지금 {emotion} 느낌이고 {modifier}조명이면 좋겠어",
]
HARD_ADJECTIVE = [
    "문장에는 {adjective}라고만 했지만 조명은 {noun_phrase}으로 잡아줘",
    "{noun_phrase}이 떠오르는 하루야. 빛도 그쪽으로 맞춰줘",
    "색 표현이 {adverbial} 느껴지게 방 조명을 조절해줘",
]
HARD_CONFLICT = [
    "{emotion}지만 색은 {noun_phrase}으로 유지해줘",
    "감정은 {emotion}인데, hue는 {noun_phrase} 쪽을 우선해줘",
]
FALLBACK_TEMPLATES = [
    "{text}. 너무 튀지 않게 부탁해",
    "{text}. 안정적인 기본 조명으로 맞춰줘",
    "{text}. 감정이 불분명하면 무난하게 해줘",
    "{text}. 밝기도 색도 중간 정도면 돼",
]
FALLBACK_TEMPLATES_INTENSITY = [
    "{text}. {modifier}느낌으로 해줘",
    "{text}. 그냥 {modifier}정도로 켜줘",
    "{text}. 색은 무난하게, {modifier}조명으로",
    "{text}. {modifier}빛이면 충분해",
]
# Training-side coverage fill for the same two lattice regions (templates disjoint from the test ones).
FILL_EMOTION_INTENSITY = [
    "{emotion}. 조명은 {modifier}느낌으로 해줘",
    "지금 {emotion}. {modifier}빛이면 좋겠어",
    "{emotion}. 색은 맡기고 {modifier}정도로만 해줘",
    "오늘 너무 {emotion}. {modifier}조명으로 바꿔줘",
]
FILL_FALLBACK_INTENSITY = [
    "{text}. {modifier}느낌이면 돼",
    "{text}. 그래도 {modifier}조명으로 해줘",
    "{text}. 무난하되 {modifier}빛으로",
]
SRC_FILL = "coverage_fill"
SRC_COMBO = "color_emotion_intensity_combinations"
SRC_HARD = "conflict_and_color_adjective_cases"
SRC_FALLBACK = "ambiguous_fallback_cases"
TEST_PROPORTIONS = {SRC_COMBO: 0.70, SRC_HARD: 0.20, SRC_FALLBACK: 0.10}


def row_key(row: dict[str, Any]) -> KeyT:
    return (str(row["input"]), row.get("emotion"), row.get("base_color"), row.get("intensity"))


def out_tuple(row: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(row["output"][k]) for k in DIMS)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---- catalogue -> training_data profile tables ------------------------------------------
PRODUCTION_COLORS = copy.deepcopy(td.COLOR_PROFILES)
PRODUCTION_EMOTIONS = copy.deepcopy(td.EMOTION_PROFILES)
PRODUCTION_INTENSITIES = copy.deepcopy(td.INTENSITY_MODIFIERS)
PRODUCTION_ADJECTIVES = copy.deepcopy(td.COLOR_ADJECTIVE_PROFILES)
PRODUCTION_ADJ_REQUIRED = copy.deepcopy(td.COLOR_ADJECTIVE_REQUIRED_CASES)
PRODUCTION_HARD = copy.deepcopy(td.TARGETED_HARD_CASES)


def build_profiles(catalog: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    colors: dict[str, Any] = {}
    for name in policy["colors"]:
        c = catalog["colors"][name]
        prod = PRODUCTION_COLORS.get(name)
        colors[name] = {
            "label": c["label"],
            "anchor_h": c["anchor_h"],
            "target": dict(c["target"]),
            "phrases": list(prod["phrases"]) if prod else list(c["phrases"]),
        }
    emotions: dict[str, Any] = {}
    for name in policy["emotions"]:
        e = catalog["emotions"][name]
        prod = PRODUCTION_EMOTIONS.get(name)
        emotions[name] = {
            "label": e["label"],
            "target": dict(e["target"]),
            "adjust": dict(e["adjust"]),
            "phrases": list(prod["phrases"]) if prod else list(e["phrases"]),
        }
    intensities = {name: copy.deepcopy(PRODUCTION_INTENSITIES[name]) for name in policy["intensities"]}
    return {"colors": colors, "emotions": emotions, "intensities": intensities}


def case_in_policy(case: dict[str, Any], prof: dict[str, Any]) -> bool:
    c, e, i = case.get("base_color"), case.get("emotion"), case.get("intensity") or "neutral"
    return (c is None or c in prof["colors"]) and (e is None or e in prof["emotions"]) and i in prof["intensities"]


class PatchedTrainingData:
    """Swap the production tables inside training_data for one policy."""

    def __init__(self, prof: dict[str, Any]):
        self.prof = prof
        self.saved: dict[str, Any] = {}

    def __enter__(self):
        names = ["COLOR_PROFILES", "EMOTION_PROFILES", "INTENSITY_MODIFIERS", "COLOR_ADJECTIVE_PROFILES",
                 "COLOR_ADJECTIVE_REQUIRED_CASES", "TARGETED_HARD_CASES", "REQUIRED_VALIDATION_CASES"]
        self.saved = {n: getattr(td, n) for n in names}
        prof = self.prof
        td.COLOR_PROFILES = prof["colors"]
        td.EMOTION_PROFILES = prof["emotions"]
        td.INTENSITY_MODIFIERS = prof["intensities"]
        td.COLOR_ADJECTIVE_PROFILES = {
            c: [e for e in entries if e["intensity"] in prof["intensities"]]
            for c, entries in PRODUCTION_ADJECTIVES.items() if c in prof["colors"]
        }
        td.COLOR_ADJECTIVE_REQUIRED_CASES = [c for c in PRODUCTION_ADJ_REQUIRED if case_in_policy(c, prof)]
        td.TARGETED_HARD_CASES = [c for c in PRODUCTION_HARD if case_in_policy(c, prof)]
        # build_required_validation_cases() hard-codes red/yellow/blue x all emotions x 5 intensities;
        # rebuild under the patched tables and drop anything outside the policy.
        td.REQUIRED_VALIDATION_CASES = [c for c in _required_cases_for(prof) if case_in_policy(c, prof)]
        return self

    def __exit__(self, *exc):
        for n, v in self.saved.items():
            setattr(td, n, v)
        return False


def _required_cases_for(prof: dict[str, Any]) -> list[dict[str, Any]]:
    cases = [
        {"text": "빨강", "emotion": None, "base_color": "red", "intensity": "neutral"},
        {"text": "빨강색", "emotion": None, "base_color": "red", "intensity": "neutral"},
        {"text": "빨간색으로 해줘", "emotion": None, "base_color": "red", "intensity": "neutral"},
        {"text": "빨갛게 켜줘", "emotion": None, "base_color": "red", "intensity": "neutral"},
        {"text": "은은한 빨강으로 해줘", "emotion": None, "base_color": "red", "intensity": "soft"},
        {"text": "화가 나서 강한 빨간색으로 해줘", "emotion": "anger", "base_color": "red", "intensity": "strong"},
        {"text": "슬프지만 붉은빛으로 표현해줘", "emotion": "sadness", "base_color": "red", "intensity": "soft"},
        {"text": "행복해서 밝은 노란색으로 해줘", "emotion": "happiness", "base_color": "yellow", "intensity": "bright"},
        {"text": "차분하게 파란색으로 켜줘", "emotion": "calm", "base_color": "blue", "intensity": "soft"},
        {"text": "불안해서 어두운 파란빛으로 해줘", "emotion": "anxiety", "base_color": "blue", "intensity": "dark"},
    ]
    cases.extend(td.COLOR_ADJECTIVE_REQUIRED_CASES)
    for color_name in ["red", "yellow", "blue"]:
        if color_name not in prof["colors"]:
            continue
        for emotion_name, emo in prof["emotions"].items():
            for intensity_name in prof["intensities"]:
                modifier = prof["intensities"][intensity_name]["label"]
                text = f"지금 {emo['phrases'][0]}. 조명은 {modifier + ' ' if modifier else ''}{prof['colors'][color_name]['label']}으로 표현해줘"
                cases.append({"text": text, "emotion": emotion_name, "base_color": color_name, "intensity": intensity_name})
    deduped: dict[str, dict[str, Any]] = {}
    for c in cases:
        deduped[c["text"]] = c
    return list(deduped.values())


# ---- train / val (mirrors prepare_datasets without base rows) ---------------------------
TRAIN_REPEAT = {"coverage_fill": 2, "synthetic_emotion": 1, "synthetic_color": 2, "synthetic_mixed": 2, "synthetic_fallback": 1,
                "targeted_hard_case": 10, "required_validation": 8, "color_adjective_sft": 3, "color_adjective_mixed_emotion": 2}
VAL_REPEAT = {"coverage_fill": 1, "synthetic_emotion": 1, "synthetic_color": 1, "synthetic_mixed": 1, "synthetic_fallback": 1,
              "targeted_hard_case": 3, "required_validation": 3, "color_adjective_sft": 1, "color_adjective_mixed_emotion": 1}


def _split_expand(rows: list[dict[str, Any]], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = list(rows)
    rng.shuffle(rows)
    split = max(1, int(len(rows) * 0.9))
    train = [dict(r) for r in rows[:split] for _ in range(TRAIN_REPEAT.get(r["source"], 1))]
    val = [dict(r) for r in rows[split:] for _ in range(VAL_REPEAT.get(r["source"], 1))]
    return train, val


def build_train_val(seed: int, coverage_fill: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # Production rows are shuffled/split exactly as prepare_datasets() does (same seed), so the
    # K240 non-fill rows reproduce the production policy-only split row for row. Coverage-fill rows
    # are split separately with a derived seed and appended.
    synthetic = td.build_synthetic_rows()
    train, val = _split_expand(synthetic, random.Random(seed))
    if coverage_fill:
        seen = {row_key(r) for r in synthetic}
        fill = [r for r in build_coverage_fill_rows() if row_key(r) not in seen]
        f_train, f_val = _split_expand(fill, random.Random(seed * 1000 + 7))
        train += f_train
        val += f_val
    return train, val


# ---- test pool (v3 benchmark builders under the patched tables) --------------------------
def build_test_pool() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mk = td.make_row
    res = td.resolve_case_output
    for e_name, e in td.EMOTION_PROFILES.items():
        for ph in e["phrases"]:
            for i_name, i in td.INTENSITY_MODIFIERS.items():
                out = res({"emotion": e_name, "intensity": i_name})
                if i_name == "neutral":
                    for t in HOLDOUT_EMOTION_ONLY:
                        rows.append(mk(text=t.format(emotion=ph), output=out, source=SRC_COMBO, emotion=e_name, base_color=None, intensity=i_name))
                else:
                    for t in HOLDOUT_EMOTION_ONLY_INTENSITY:
                        rows.append(mk(text=t.format(emotion=ph, modifier=f"{i['label']} "), output=out, source=SRC_COMBO, emotion=e_name, base_color=None, intensity=i_name))
    for c_name, c in td.COLOR_PROFILES.items():
        for ph in c["phrases"]:
            for i_name, i in td.INTENSITY_MODIFIERS.items():
                mod = f"{i['label']} " if i["label"] else ""
                out = res({"base_color": c_name, "intensity": i_name})
                for t in HOLDOUT_COLOR_ONLY:
                    rows.append(mk(text=t.format(modifier=mod, color=ph), output=out, source=SRC_COMBO, emotion=None, base_color=c_name, intensity=i_name))
    for e_name, e in td.EMOTION_PROFILES.items():
        for c_name, c in td.COLOR_PROFILES.items():
            for i_name, i in td.INTENSITY_MODIFIERS.items():
                mod = f"{i['label']} " if i["label"] else ""
                out = res({"emotion": e_name, "base_color": c_name, "intensity": i_name})
                for eph in e["phrases"][:4]:
                    for cph in c["phrases"][:4]:
                        for t in HOLDOUT_MIXED:
                            rows.append(mk(text=t.format(emotion=eph, modifier=mod, color=cph), output=out, source=SRC_COMBO, emotion=e_name, base_color=c_name, intensity=i_name))
    for c_name, entries in td.COLOR_ADJECTIVE_PROFILES.items():
        for entry in entries:
            out = res({"base_color": c_name, "intensity": entry["intensity"]})
            for t in HARD_ADJECTIVE:
                rows.append(mk(text=t.format(emotion="무난한", **entry), output=out, source=SRC_HARD, emotion=None, base_color=c_name, intensity=entry["intensity"]))
            for e_name, e in td.EMOTION_PROFILES.items():
                out = res({"base_color": c_name, "emotion": e_name, "intensity": entry["intensity"]})
                for eph in e["phrases"][:3]:
                    for t in HARD_CONFLICT:
                        rows.append(mk(text=t.format(emotion=eph, **entry), output=out, source=SRC_HARD, emotion=e_name, base_color=c_name, intensity=entry["intensity"]))
    for case in td.TARGETED_HARD_CASES:
        out = res(case)
        for suffix in ("조금 더 명확하게", "과하지 않게", "테스트용으로"):
            rows.append(mk(text=f"{case['text']} - {suffix} 표현해줘", output=out, source=SRC_HARD, emotion=case.get("emotion"), base_color=case.get("base_color"), intensity=case.get("intensity")))
    for text in td.AMBIGUOUS_INPUTS:
        for i_name, i in td.INTENSITY_MODIFIERS.items():
            out = res({"intensity": i_name})
            if i_name == "neutral":
                for t in FALLBACK_TEMPLATES:
                    rows.append(mk(text=t.format(text=text), output=td.SAFE_FALLBACK, source=SRC_FALLBACK, emotion=None, base_color=None, intensity=i_name))
            else:
                for t in FALLBACK_TEMPLATES_INTENSITY:
                    rows.append(mk(text=t.format(text=text, modifier=f"{i['label']} "), output=out, source=SRC_FALLBACK, emotion=None, base_color=None, intensity=i_name))
    return rows


def build_coverage_fill_rows() -> list[dict[str, Any]]:
    """Rows for (emotion, no colour, non-neutral intensity) and (fallback, non-neutral intensity):
    the production generator never emits these, leaving 21/240 reachable tuples untrained."""
    rows: list[dict[str, Any]] = []
    for e_name, e in td.EMOTION_PROFILES.items():
        for i_name, i in td.INTENSITY_MODIFIERS.items():
            if i_name == "neutral":
                continue
            out = td.resolve_case_output({"emotion": e_name, "intensity": i_name})
            for ph in e["phrases"][:6]:
                for t in FILL_EMOTION_INTENSITY:
                    rows.append(td.make_row(text=t.format(emotion=ph, modifier=f"{i['label']} "), output=out, source=SRC_FILL, emotion=e_name, base_color=None, intensity=i_name))
    for text in td.AMBIGUOUS_INPUTS:
        for i_name, i in td.INTENSITY_MODIFIERS.items():
            if i_name == "neutral":
                continue
            out = td.resolve_case_output({"intensity": i_name})
            for t in FILL_FALLBACK_INTENSITY:
                rows.append(td.make_row(text=t.format(text=text, modifier=f"{i['label']} "), output=out, source=SRC_FILL, emotion=None, base_color=None, intensity=i_name))
    return rows


def sample_test(pool: list[dict[str, Any]], blocked: set[KeyT], reachable: set[tuple[int, ...]], total: int,
                min_per_tuple: int, rng: random.Random) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # dedupe against train/val and inside the pool
    seen: set[KeyT] = set(blocked)
    pool_d: list[dict[str, Any]] = []
    for r in pool:
        k = row_key(r)
        if k in seen:
            continue
        seen.add(k)
        pool_d.append(r)
    rng.shuffle(pool_d)
    by_tuple: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in pool_d:
        by_tuple[out_tuple(r)].append(r)
    chosen: list[dict[str, Any]] = []
    chosen_ids: set[int] = set()
    uncovered = []
    for t in sorted(reachable):
        cands = by_tuple.get(t, [])
        cands.sort(key=lambda r: 0 if r["source"] == SRC_COMBO else 1)  # prefer combination rows for coverage
        take = cands[:min_per_tuple]
        if len(take) < min_per_tuple:
            uncovered.append((t, len(take)))
        for r in take:
            chosen.append(r); chosen_ids.add(id(r))
    remaining = [r for r in pool_d if id(r) not in chosen_ids]
    by_src: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in remaining:
        by_src[r["source"]].append(r)
    budget = max(0, total - len(chosen))
    # fill by production proportion, computed on the FINAL composition target
    target_counts = {s: int(round(total * p)) for s, p in TEST_PROPORTIONS.items()}
    have = Counter(r["source"] for r in chosen)
    fill: list[dict[str, Any]] = []
    for s in (SRC_COMBO, SRC_HARD, SRC_FALLBACK):
        need = max(0, target_counts[s] - have[s])
        take = by_src[s][:min(need, len(by_src[s]))]
        fill.extend(take)
        by_src[s] = by_src[s][len(take):]
    fill = fill[:budget]
    if len(fill) < budget:  # top up from whatever remains, combination rows first
        leftovers = by_src[SRC_COMBO] + by_src[SRC_HARD] + by_src[SRC_FALLBACK]
        fill.extend(leftovers[: budget - len(fill)])
    chosen.extend(fill)
    rng.shuffle(chosen)
    info = {"pool_rows": len(pool), "pool_unique_after_dedupe": len(pool_d), "selected": len(chosen),
            "requested": total, "min_per_tuple": min_per_tuple, "tuples_short_of_min": uncovered}
    return chosen, info


def tuple_coverage(rows: list[dict[str, Any]], reachable: set[tuple[int, ...]]) -> dict[str, Any]:
    c = Counter(out_tuple(r) for r in rows)
    covered = [t for t in reachable if c[t] > 0]
    return {"reachable": len(reachable), "covered": len(covered), "missing": [list(t) for t in reachable if c[t] == 0],
            "min_rows_per_tuple": min((c[t] for t in reachable), default=0), "median_rows_per_tuple": sorted(c[t] for t in reachable)[len(reachable) // 2] if reachable else 0,
            "off_policy_rows": sum(n for t, n in c.items() if t not in reachable)}


def reachable_tuples(prof: dict[str, Any]) -> set[tuple[int, ...]]:
    out: set[tuple[int, ...]] = set()
    for c in [None] + list(prof["colors"]):
        for e in [None] + list(prof["emotions"]):
            for i in prof["intensities"]:
                o = td.normalize_output(td.resolve_case_output({"base_color": c, "emotion": e, "intensity": i}))
                out.add(tuple(o[k] for k in DIMS))
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "keff_policies.json")
    ap.add_argument("--out-root", type=Path, default=REPO_ROOT / "backend" / "models" / "compact_llm" / "datasets" / "keff_series")
    ap.add_argument("--policies", nargs="*", default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-rows", type=int, default=2000)
    ap.add_argument("--min-per-tuple", type=int, default=2)
    ap.add_argument("--no-coverage-fill", action="store_true",
                    help="reproduce the production generator exactly (leaves emotion-only x intensity and fallback x intensity tuples untrained)")
    ap.add_argument("--include-natural", type=Path, default=None,
                    help="optional jsonl of base_train natural rows to append to train_100 (W-series parity)")
    ap.add_argument("--compare-policy-only", type=Path,
                    default=REPO_ROOT / "backend" / "models" / "compact_llm" / "datasets" / "policy_only" / "train_policy_48035.jsonl",
                    help="production policy-only train file; K240 output is compared against it")
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    catalog = cfg["catalog"]
    names = args.policies or sorted(cfg["policies"], key=lambda n: cfg["policies"][n]["k_eff_target"])
    natural = load_jsonl(args.include_natural) if args.include_natural else None
    series: dict[str, Any] = {"config": str(args.config.relative_to(REPO_ROOT)), "config_sha256": sha256_file(args.config),
                              "seed": args.seed, "policies": {}}
    for name in names:
        pol = cfg["policies"][name]
        prof = build_profiles(catalog, pol)
        out_dir = args.out_root / name
        with PatchedTrainingData(prof):
            reach = reachable_tuples(prof)
            assert len(reach) == pol["k_eff_target"], (name, len(reach))
            train, val = build_train_val(args.seed, coverage_fill=not args.no_coverage_fill)
            blocked = {row_key(r) for r in train} | {row_key(r) for r in val}
            pool = build_test_pool()
            test, tinfo = sample_test(pool, blocked, reach, args.test_rows, args.min_per_tuple, random.Random(args.seed + 1))
            policy_json = {
                "policy": name, "k_eff": len(reach),
                "system_prompt": td.SYSTEM_PROMPT,
                "color_anchors": {n: {"hue": p["anchor_h"], "target": p["target"], "label": p["label"], "phrases": p["phrases"]} for n, p in prof["colors"].items()},
                "emotion_profiles": {n: {"target": p["target"], "adjust": p["adjust"], "label": p["label"], "phrases": p["phrases"]} for n, p in prof["emotions"].items()},
                "intensity_adjustments": {n: p["adjust"] for n, p in prof["intensities"].items()},
                "safe_fallback": td.SAFE_FALLBACK,
                "hue_policy": "Explicit color requests keep hue within distance <= 18 of the color anchor; emotion and intensity adjust S/B/Dimmer/CT primarily.",
                "reachable_tuples": sorted(list(t) for t in reach),
            }
        if natural is not None:
            train = td.enrich_base_rows(natural, "base_train") + train
        # sanity: train/val/test keys disjoint
        tv_keys = {row_key(r) for r in train} | {row_key(r) for r in val}
        assert all(row_key(r) not in tv_keys for r in test), "test leaks into train/val"
        by_input: dict[str, set[tuple[int, ...]]] = defaultdict(set)
        for r in test:
            by_input[r["input"]].add(out_tuple(r))
        ambiguous_inputs = sorted(i for i, outs in by_input.items() if len(outs) > 1)
        assert not ambiguous_inputs, f"{name}: {len(ambiguous_inputs)} test inputs carry conflicting gold tuples"
        write_jsonl(out_dir / "train_100.jsonl", train)
        write_jsonl(out_dir / "val.jsonl", val)
        write_jsonl(out_dir / "test_rule.jsonl", test)
        (out_dir / "policy.json").write_text(json.dumps(policy_json, ensure_ascii=False, indent=1), encoding="utf-8")
        man = {
            "policy": name, "k_eff": len(reach),
            "colors": pol["colors"], "emotions": pol["emotions"], "intensities": pol["intensities"],
            "rows": {"train_100": len(train), "val": len(val), "test_rule": len(test)},
            "train_by_source": dict(sorted(Counter(r["source"] for r in train).items())),
            "test_by_source": dict(sorted(Counter(r["source"] for r in test).items())),
            "coverage": {"train": tuple_coverage(train, reach), "val": tuple_coverage(val, reach), "test": tuple_coverage(test, reach)},
            "test_sampling": tinfo,
            "coverage_fill": not args.no_coverage_fill,
            "test_ambiguous_inputs": 0,
            "sha256": {f: sha256_file(out_dir / f) for f in ("train_100.jsonl", "val.jsonl", "test_rule.jsonl", "policy.json")},
        }
        if name == "K240" and args.compare_policy_only and args.compare_policy_only.exists():
            prod = Counter((r["input"], out_tuple(r)) for r in load_jsonl(args.compare_policy_only))
            ours = Counter((r["input"], out_tuple(r)) for r in train if r["source"] not in ("base_train", SRC_FILL))
            inter = sum((prod & ours).values())
            man["k240_vs_production_policy_only"] = {
                "production_rows": sum(prod.values()), "generated_rows": sum(ours.values()),
                "multiset_overlap_rows": inter,
                "production_unique_inputs": len({k[0] for k in prod}), "generated_unique_inputs": len({k[0] for k in ours}),
                "inputs_only_in_production": len({k[0] for k in prod} - {k[0] for k in ours}),
                "inputs_only_in_generated": len({k[0] for k in ours} - {k[0] for k in prod}),
                "label_disagreements_on_shared_inputs": sum(1 for (inp, t) in ours if (inp, t) not in prod and any(k[0] == inp for k in prod)),
            }
        (out_dir / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        series["policies"][name] = {k: man[k] for k in ("k_eff", "rows", "coverage", "sha256")} | ({"k240_vs_production_policy_only": man["k240_vs_production_policy_only"]} if "k240_vs_production_policy_only" in man else {})
        cov = man["coverage"]
        print(f"{name}: K_eff={len(reach)} train={len(train)} val={len(val)} test={len(test)} | "
              f"train covers {cov['train']['covered']}/{len(reach)} (min {cov['train']['min_rows_per_tuple']}/tuple), "
              f"test covers {cov['test']['covered']}/{len(reach)} (min {cov['test']['min_rows_per_tuple']}/tuple) | test by source {man['test_by_source']}")
        if tinfo["tuples_short_of_min"]:
            print(f"   WARNING {name}: {len(tinfo['tuples_short_of_min'])} tuples below min_per_tuple in the pool")
    (args.out_root / "keff_series_manifest.json").write_text(json.dumps(series, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
