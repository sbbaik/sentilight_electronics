"""Blinded author audit of machine-generated items.

This is an internal quality audit of generated data, not a study on participants and not an independent user evaluation.
The authors read 60 machine-written utterances with the gold tuple hidden and record only what they can judge from the
sentence: which colour, emotion and intensity it expresses, whether the meaning is unambiguous, and whether the Korean
is severely unnatural. The answer key is written to a separate file that the auditors are not to open first.

Sampling: 5 items from each of the 12 cells of the 3 lexical-overlap bands x 4 utterance-length bands, drawn with a
fixed seed. Cells holding fewer than 5 items contribute all of them and are marked.

Nothing in the released data or in any reported result may be changed on the basis of this audit; a disagreement is
reported as an error rate and as a limitation.
Outputs: report/20260913_blinded_author_audit_sheet.md (blinded) and
backend/models/compact_llm/datasets/holdout_paraphrase/K240/audit_answer_key.json (keep closed until the sheet is filled).
"""
from __future__ import annotations
import json, random
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; P2 = REPO.parent
D = REPO / "backend/models/compact_llm/datasets/holdout_paraphrase/K240"
DIMS = ("H", "S", "B", "Dimmer", "CT")
rows = [json.loads(l) for l in (D / "holdout_paraphrase.jsonl").open(encoding="utf-8")]
def lexband(r):
    L = r["lexical"]
    return "all" if L["all_named_attributes_use_catalogue_wording"] else ("none" if L["no_named_attribute_uses_catalogue_wording"] else "partial")
def lenband(r):
    n = r["char_len"]
    return "<=25" if n <= 25 else ("26-45" if n <= 45 else ("46-65" if n <= 65 else ">=66"))
cells = {}
for r in rows: cells.setdefault((lexband(r), lenband(r)), []).append(r)
rng = random.Random(20260913)
picked, notes = [], []
for lex in ("all", "partial", "none"):
    for ln in ("<=25", "26-45", "46-65", ">=66"):
        pool = cells.get((lex, ln), [])
        take = rng.sample(pool, min(5, len(pool)))
        if len(take) < 5: notes.append(f"cell ({lex}, {ln}) holds only {len(pool)} items; all of them are included")
        for r in take: picked.append({"lex": lex, "len": ln, **r})
rng.shuffle(picked)
sheet = [
"# Blinded author audit of machine-generated items", "",
"이 작업은 **생성 데이터의 내부 품질 감사**다. 참가자를 대상으로 하는 연구가 아니고, 독립적인 사용자 평가도 아니다.",
"기존 20명 조명 선호도 평가와는 완전히 별개이며 서로 섞어서 서술하지 않는다.", "",
"## 방법", "",
"- 아래 60개 문장은 정답 튜플을 숨긴 상태로 제시된다. 정답표는 별도 파일에 있으며 작성 전에 열지 않는다.",
"- 저자는 문장만 읽고 다음 네 가지를 기록한다.",
"  1. **색상**: red / yellow / blue / green / purple / orange / white / none",
"  2. **감정**: sadness / happiness / anger / calm / anxiety / none",
"  3. **강도**: soft / strong / bright / dark / neutral",
"  4. **의미 명확성**: 하나로 정해지는가 (예 / 아니오). 아니오면 무엇이 모호한지 메모",
"  5. **심각한 부자연성**: 한국어로 심하게 어색한가 (예 / 아니오). 예면 무엇이 어색한지 메모",
"- 위 다섯 가지 외에는 기록하지 않는다. 문장의 좋고 나쁨이나 선호는 평가 대상이 아니다.",
"- 작성이 끝난 뒤에만 정답표와 대조하고, 불일치율을 보충자료 S14에 보고한다.",
"- **검수 결과로 데이터나 평가 결과를 수정하지 않는다.** 문제가 발견되면 오류율과 한계로만 보고한다.", "",
"## 문장", "",
"| # | 문장 | 색상 | 감정 | 강도 | 의미 명확 | 심각한 부자연성 | 메모 |",
"|--:|---|---|---|---|---|---|---|"]
for i, r in enumerate(picked, 1):
    sheet.append(f"| {i} | {r['input']} |  |  |  |  |  |  |")
sheet += ["", "## 표집", "",
          "어휘 중첩 3구간 × 문장 길이 4구간의 12개 셀에서 각 5행씩, 고정 난수(seed 20260913)로 추출했다. 제시 순서는 무작위로 섞었다."]
if notes: sheet += ["", "다음 셀은 5행에 미치지 못해 보유분을 모두 포함했다:"] + [f"- {n}" for n in notes]
(P2 / "report/20260913_blinded_author_audit_sheet.md").write_text("\n".join(sheet) + "\n", encoding="utf-8")
key = {"do_not_open_before_filling_the_sheet": True,
       "note": "internal quality audit of generated data; not a human-subjects study",
       "items": [{"n": i, "input": r["input"], "lexical_band": r["lex"], "length_band": r["len"],
                  "target_color": r["base_color"], "target_emotion": r["emotion"], "target_intensity": r["intensity"],
                  "gold_tuple": {k: int(r["output"][k]) for k in DIMS}} for i, r in enumerate(picked, 1)]}
(D / "audit_answer_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"sheet: {len(picked)} items; cells short of 5: {len(notes)}")
for n in notes: print("  " + n)
