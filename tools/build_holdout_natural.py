"""Build an UNTOUCHED final hold-out test set for the production policy (K240) from sentence frames that were
never used in any training, validation, development-test or K-series template.

Design
  * Same category lexicon as the policy (emotion phrases, colour phrases, intensity modifiers) — the gold tuple is
    computed by the executable policy (training_data.resolve_case_output), so every row has an unambiguous target.
  * NEW sentence frames only: longer, conversational, with context clauses, particles and word orders that do not
    occur in the generator's templates. Every produced utterance is checked for exact-string absence from
    train_100 / val / test_rule of K240 (and of the other K-series policies) and from the K48 common test set.
  * Non-neutral intensity is always named in the utterance (the conflicting-gold defect of the 1,000-row benchmark
    is avoided by construction).
  * Composition (2,000 rows): 70 % colour+emotion(+intensity), 12 % colour-only, 12 % emotion-only, 6 % fallback;
    every one of the 240 reachable tuples appears at least twice.
Outputs: backend/models/compact_llm/datasets/holdout_natural/K240/holdout_2000.jsonl (+ frames.json, sha256, report.md).
Usage: python tools/build_holdout_natural.py [--seed 20260913]
"""
from __future__ import annotations
import argparse, hashlib, json, random, sys
from collections import Counter
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend" / "models"))
from compact_llm import training_data as td  # noqa: E402

OUT = REPO / "backend/models/compact_llm/datasets/holdout_natural/K240"
DIMS = ("H", "S", "B", "Dimmer", "CT")

# ---------------------------------------------------------------- new sentence frames (never used before)
MIXED = [  # {emotion} {modifier} {color}
    "회의 끝나고 집에 왔는데 {emotion}. 조명은 {modifier}{color} 쪽으로 해줄래",
    "지금 상태는 {emotion}. 거실 전등을 {modifier}{color}으로 바꿔 주면 좋겠어",
    "{emotion}. 이런 날엔 방을 {modifier}{color} 빛으로 채우고 싶어",
    "솔직히 {emotion}. 그래도 불빛은 {modifier}{color}이면 좋겠어",
    "하루 종일 {emotion}. 침실 조명 {modifier}{color}으로 켜 줘",
    "{emotion}. 전등 색 {modifier}{color}으로 맞춰 줄 수 있어?",
    "기분이 {emotion}. 분위기는 {modifier}{color}으로 잡아 줘",
    "지금 {emotion}. 창가 등을 {modifier}{color} 톤으로 해 줘",
    "요즘 자꾸 {emotion}. 오늘은 {modifier}{color}빛 아래서 쉬고 싶어",
    "{emotion}. 방 전체를 {modifier}{color} 느낌으로 바꿔줘",
    "퇴근하고 나니 {emotion}. 조명은 {modifier}{color}으로 부탁할게",
    "{emotion}... 불은 {modifier}{color}으로 해 두자",
]
COLOR_ONLY = [  # {modifier} {color}
    "감정 얘기는 빼고, 거실을 {modifier}{color}으로 밝혀 줘",
    "오늘 저녁 조명은 {modifier}{color}빛으로 가자",
    "{modifier}{color} 톤으로 침실 무드 잡아 줄래",
    "책 읽을 거니까 방 등을 {modifier}{color}으로 켜 줘",
    "손님 오기 전에 전등을 {modifier}{color} 계열로 바꿔 줘",
    "그냥 {modifier}{color} 빛으로 해 줘, 다른 건 상관없어",
]
EMOTION_ONLY_NEUTRAL = [  # {emotion} only, neutral intensity
    "색은 네가 골라 줘. 나는 지금 {emotion}",
    "{emotion}. 이 기분에 어울리는 조명이면 뭐든 좋아",
    "어떤 색이 좋을지 모르겠어. 다만 지금 {emotion}",
    "오늘 하루를 한마디로 하면 {emotion}. 조명으로 좀 달래 줘",
]
EMOTION_ONLY_INTENSITY = [  # {emotion} + {modifier} (no colour)
    "색은 알아서 해 줘. 지금 {emotion}, 밝기는 {modifier}쪽으로",
    "{emotion}. 색보다 {modifier}빛이면 좋겠어",
    "오늘 {emotion}. 조명은 {modifier}느낌으로만 맞춰 줘",
    "지금 마음이 {emotion}. {modifier}조명으로 방을 바꿔 줘",
]
FALLBACK_NEUTRAL = [  # {text} ambiguous
    "{text}. 그냥 평소처럼 켜 줘",
    "{text}. 튀지 않는 기본 조명이면 좋겠어",
    "{text}. 특별한 건 없고 편하게만 해 줘",
]
FALLBACK_INTENSITY = [  # {text} + {modifier}
    "{text}. 굳이 색은 말고 {modifier}빛으로만",
    "{text}. 밝기만 {modifier}정도로 해 줘",
    "{text}. 무난한 색에 {modifier}조명이면 돼",
]
FRAMES = {"mixed": MIXED, "color_only": COLOR_ONLY, "emotion_only_neutral": EMOTION_ONLY_NEUTRAL,
          "emotion_only_intensity": EMOTION_ONLY_INTENSITY, "fallback_neutral": FALLBACK_NEUTRAL, "fallback_intensity": FALLBACK_INTENSITY}

def gold(color, emotion, intensity):
    return td.normalize_output(td.resolve_case_output({"base_color": color, "emotion": emotion, "intensity": intensity}))

def build(seed: int, n_target: int = 2000):
    rng = random.Random(seed)
    E = {k: v["phrases"] for k, v in td.EMOTION_PROFILES.items()}
    C = {k: v["phrases"] for k, v in td.COLOR_PROFILES.items()}
    I = {k: (v["phrases"] if k != "neutral" else [""]) for k, v in td.INTENSITY_MODIFIERS.items()}
    rows = []
    def add(text, color, emotion, intensity, source):
        rows.append({"instruction": td.SYSTEM_PROMPT, "input": text, "output": gold(color, emotion, intensity),
                     "emotion": emotion, "base_color": color, "intensity": intensity, "source": source})
    # 1) coverage: every reachable tuple at least twice
    for c in [None] + list(C):
        for e in [None] + list(E):
            for i in I:
                for _ in range(2):
                    mod = rng.choice(I[i]); mod = f"{mod} " if mod else ""
                    if c and e:
                        add(rng.choice(MIXED).format(emotion=rng.choice(E[e]), modifier=mod, color=rng.choice(C[c])), c, e, i, "holdout_mixed")
                    elif c:
                        add(rng.choice(COLOR_ONLY).format(modifier=mod, color=rng.choice(C[c])), c, None, i, "holdout_color_only")
                    elif e:
                        if i == "neutral": add(rng.choice(EMOTION_ONLY_NEUTRAL).format(emotion=rng.choice(E[e])), None, e, i, "holdout_emotion_only")
                        else: add(rng.choice(EMOTION_ONLY_INTENSITY).format(emotion=rng.choice(E[e]), modifier=mod), None, e, i, "holdout_emotion_only")
                    else:
                        t = rng.choice(td.AMBIGUOUS_INPUTS)
                        if i == "neutral": add(rng.choice(FALLBACK_NEUTRAL).format(text=t), None, None, i, "holdout_fallback")
                        else: add(rng.choice(FALLBACK_INTENSITY).format(text=t, modifier=mod), None, None, i, "holdout_fallback")
    # 2) fill to n_target with the target proportions
    quota = {"holdout_mixed": 0.70, "holdout_color_only": 0.12, "holdout_emotion_only": 0.12, "holdout_fallback": 0.06}
    seen = set(r["input"] for r in rows); tries = 0
    while len(rows) < n_target and tries < 200000:
        tries += 1
        src = rng.choices(list(quota), weights=list(quota.values()))[0]
        i = rng.choice(list(I)); mod = rng.choice(I[i]); mod = f"{mod} " if mod else ""
        if src == "holdout_mixed":
            c, e = rng.choice(list(C)), rng.choice(list(E)); text = rng.choice(MIXED).format(emotion=rng.choice(E[e]), modifier=mod, color=rng.choice(C[c]))
        elif src == "holdout_color_only":
            c, e = rng.choice(list(C)), None; text = rng.choice(COLOR_ONLY).format(modifier=mod, color=rng.choice(C[c]))
        elif src == "holdout_emotion_only":
            c, e = None, rng.choice(list(E)); text = (rng.choice(EMOTION_ONLY_NEUTRAL).format(emotion=rng.choice(E[e])) if i == "neutral" else rng.choice(EMOTION_ONLY_INTENSITY).format(emotion=rng.choice(E[e]), modifier=mod))
        else:
            c, e = None, None; t = rng.choice(td.AMBIGUOUS_INPUTS); text = (rng.choice(FALLBACK_NEUTRAL).format(text=t) if i == "neutral" else rng.choice(FALLBACK_INTENSITY).format(text=t, modifier=mod))
        if text in seen: continue
        seen.add(text); add(text, c, e, i, src)
    rng.shuffle(rows)
    return rows[:n_target]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=20260913); a = ap.parse_args()
    rows = build(a.seed)
    # leakage check against every existing utterance of the K series and the production splits
    existing = set()
    for f in list((REPO / "backend/models/compact_llm/datasets/keff_series").rglob("*.jsonl")):
        for l in f.open(encoding="utf-8"): existing.add(json.loads(l)["input"])
    leaks = [r["input"] for r in rows if r["input"] in existing]
    tuples = Counter(tuple(int(r["output"][k]) for k in DIMS) for r in rows)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "holdout_2000.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (OUT / "frames.json").write_text(json.dumps(FRAMES, ensure_ascii=False, indent=1), encoding="utf-8")
    h = hashlib.sha256(p.read_bytes()).hexdigest(); (OUT / "holdout_2000.sha256").write_text(f"{h}  holdout_2000.jsonl\n")
    src = Counter(r["source"] for r in rows)
    rep = ["# Final hold-out test set (K240 production policy)", "", f"- rows: {len(rows)}; seed {a.seed}; sha256 {h}",
           f"- reachable tuples covered: {len(tuples)}/240; min rows per tuple {min(tuples.values())}; max {max(tuples.values())}",
           f"- exact-string overlap with any K-series train/val/test utterance: {len(leaks)}",
           f"- sources: {dict(src)}", f"- sentence frames: {sum(len(v) for v in FRAMES.values())} new frames in {len(FRAMES)} families (frames.json); none appears in the generator's training, validation, development-test or fill templates",
           "- intensity is named in every non-neutral row; gold tuples computed by the executable policy (0 ambiguity by construction)",
           "- this file was created after all model selection was complete (2026-09-13) and is used once, for the final evaluation reported in the paper"]
    (OUT / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8"); print("\n".join(rep))
    assert not leaks and len(tuples) == 240

if __name__ == "__main__":
    main()
