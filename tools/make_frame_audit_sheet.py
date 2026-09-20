"""Blinded author audit of the 32 template frames of the unseen-frame hold-out.

Internal quality audit of generated data by the authors, the same kind of check as the paraphrase audit and likewise not
a study on participants. Each frame is shown with three example sentences and the authors record whether the Korean is
natural and whether the intended attributes are unambiguous. Nothing in the released data or the reported results may be
changed on the basis of the audit; disagreements are reported as an error rate and as a limitation.
Output: report/20260913_frame_audit_sheet.md
"""
from __future__ import annotations
import json, random, re
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; P2 = REPO.parent
P = REPO / "backend/models/compact_llm/datasets/holdout_natural/K240"
rows = [json.loads(l) for l in (P / "holdout_2000.jsonl").open(encoding="utf-8")]
frames = json.loads((P / "frames.json").read_text(encoding="utf-8"))
pats = []
for fam, lst in frames.items():
    for i, f in enumerate(lst):
        pat = re.escape(f)
        for ph in ("\\{emotion\\}", "\\{modifier\\}", "\\{color\\}", "\\{text\\}"): pat = pat.replace(ph, "(?:.*?)")
        pats.append((fam, f"{fam}#{i+1}", f, re.compile("^" + pat + "$")))
rng = random.Random(20260913)
out = ["# Blinded author audit of the hold-out sentence frames", "",
"생성 데이터의 내부 품질 감사다. 참가자 대상 연구가 아니며, 기존 20명 조명 선호도 평가와 완전히 별개다.", "",
"32개 프레임 각각에 예시 3문장을 제시한다. 저자는 두 가지만 1–5로 기록한다.", "",
"- **자연성**: 한국어로 자연스러운 문장인가 (1 전혀 아니다 … 5 매우 그렇다)",
"- **의미 명확성**: 색상·감정·강도 해석이 하나로 정해지는가 (모호하면 낮게)", "",
"평정자 2인이 독립 작성한 뒤 차이가 2 이상인 프레임만 합의한다. 평균 3.0 미만 프레임은 보충자료에 한계로 기재한다.",
"**검수 결과로 데이터나 평가 결과를 수정하지 않는다.**", "",
"| 프레임 | 가족 | 예시 문장 | 자연성(1–5) | 의미 명확성(1–5) | 메모 |", "|---|---|---|---|---|---|"]
for fam, fid, tmpl, rx in pats:
    ex = [r["input"] for r in rows if rx.match(r["input"])]
    out.append(f"| {fid} | {fam} | " + "<br>".join(rng.sample(ex, min(3, len(ex)))) + " |  |  |  |")
(P2 / "report/20260913_frame_audit_sheet.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"frame audit sheet: {len(pats)} frames")
