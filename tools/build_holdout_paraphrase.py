"""Build a paraphrase hold-out: a second unseen-frame evaluation set whose utterances are written by an external large
language model rather than by sentence templates, so that lexical and syntactic variety is not bounded by 32 frames.

No human subjects are involved. The gold tuple is still defined by the executable policy: every utterance is generated
FOR a target attribute triple (colour, emotion, intensity), and the policy resolves that triple to the command tuple.

Two safeguards make the gold trustworthy.
  1. Generation is constrained: the prompt states which attributes must be expressed and which must NOT be mentioned
     (a colour named in a colour-free cell, or an intensity named in a neutral cell, would change the gold).
  2. Blind back-labelling: every candidate is shown alone, without its target, to the same model in a separate pass
     that must name the colour, emotion and intensity it expresses. Only candidates whose back-label reproduces the
     target triple are kept. The yield is reported. This is round-trip consistency, not ground truth, and it shares a
     model with the generator; a sample is written out for author spot-checking.

Every kept row is tagged with lexical novelty: whether it contains any phrase from the policy catalogue for its target
colour / emotion / intensity. Accuracy can then be split by how far the wording departs from the training lexicon,
which is the quantity the paper's conclusion is about.

Outputs backend/models/compact_llm/datasets/holdout_paraphrase/K240/{holdout_paraphrase.jsonl, candidates.jsonl,
rejected.jsonl, spotcheck_sample.md, report.md, *.sha256}.
Usage: python tools/build_holdout_paraphrase.py [--per-cell 12] [--target 2000] [--workers 8]
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, re, sys, threading, time, urllib.error, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO / "backend/models"))
from compact_llm import training_data as td  # noqa: E402
OUT = REPO / "backend/models/compact_llm/datasets/holdout_paraphrase/K240"
CACHE = OUT / ".cache"
DIMS = ("H", "S", "B", "Dimmer", "CT")
MODEL = "gemini-3.1-flash-lite"
KEY = os.environ.get("GEMINI_API_KEY", "")
KO_COLOR = {"red": "빨강", "yellow": "노랑", "blue": "파랑", "green": "초록", "purple": "보라", "orange": "주황", "white": "하양"}
KO_EMOTION = {"sadness": "슬픔/우울", "happiness": "기쁨/행복", "anger": "분노/짜증", "calm": "평온/차분", "anxiety": "불안/초조"}
KO_INTENSITY = {"neutral": "(밝기 언급 없음)", "soft": "은은함/부드러움", "strong": "강렬함/진함", "bright": "밝음", "dark": "어두움"}
_lock = threading.Lock(); _calls = [0]

def gemini(prompt: str, temperature: float, retries: int = 5) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL}:generateContent?key={KEY}"
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096}}
    last = None
    for a in range(retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=180))
            with _lock: _calls[0] += 1
            return r["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:                       # rate limit, transient 5xx, malformed reply
            last = e; time.sleep(min(2 ** a, 30) + random.random())
    raise RuntimeError(f"gemini failed after {retries}: {last}")

def parse_array(text: str) -> list[str]:
    m = re.search(r"\[.*\]", text, re.S)
    if not m: return []
    try: arr = json.loads(m.group(0))
    except Exception: return []
    return [str(x).strip() for x in arr if isinstance(x, (str,)) and str(x).strip()]

def cached(name: str, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.sha256(name.encode()).hexdigest()[:32] + ".json")
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except Exception: pass
    v = fn(); f.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8"); return v

# ---------------------------------------------------------------- generation
def gen_prompt(color, emotion, intensity, n):
    must, forbid = [], []
    if color: must.append(f"조명 색으로 {KO_COLOR[color]} 계열을 원한다는 뜻이 분명히 드러날 것")
    else: forbid.append("어떤 색 이름도 말하지 말 것 (빨강·노랑·파랑·초록·보라·주황·하양 및 그 변형, 색을 가리키는 비유 포함)")
    if emotion: must.append(f"화자의 감정이 {KO_EMOTION[emotion]}임이 드러날 것")
    else: forbid.append("기쁨·슬픔·분노·평온·불안 중 어떤 감정도 드러내지 말 것")
    if intensity != "neutral": must.append(f"밝기/세기를 {KO_INTENSITY[intensity]} 쪽으로 원한다는 뜻이 드러날 것")
    else: forbid.append("밝기나 세기를 가리키는 말(밝은·어두운·은은한·강한·진한 등)을 쓰지 말 것")
    if not color and not emotion:
        must.append("무엇을 원하는지 뚜렷하지 않은, 애매하고 일상적인 요청일 것")
    return f"""너는 한국어 스마트 조명 앱에 사람들이 실제로 입력할 법한 문장을 만드는 역할이다.

아래 조건을 만족하는 서로 다른 한국어 문장 {n}개를 만들어라.

반드시 드러나야 하는 것:
{chr(10).join('- ' + x for x in must) if must else '- (없음)'}

절대 하지 말 것:
{chr(10).join('- ' + x for x in forbid) if forbid else '- (없음)'}

문장 작성 지침:
- 어휘를 최대한 다양하게 써라. 뻔한 단어만 쓰지 말고, 같은 뜻의 드문 표현·비유·구어체도 섞어라.
  (예: 주황이면 '귤빛', '노을빛', '살구색' 같은 표현도 좋다. 단 색을 금지한 경우에는 절대 쓰지 마라.)
- 문장 구조도 다양하게 하라. 짧은 명령, 긴 서술, 반말과 존댓말, 도치, 이유를 덧붙인 문장을 섞어라.
- 실제 사람이 앱에 말하듯 자연스러워야 한다. 번역투를 쓰지 마라.
- 길이를 고루 섞어라. 만드는 문장 중 3분의 1은 짧게(12~25자), 3분의 1은 보통(25~45자), 3분의 1은 길게(45~85자) 하라.
- 짧은 문장도 반드시 포함하라. 사람들은 앱에 짧게 말하는 경우가 많다.
- 설명 없이 JSON 문자열 배열만 출력하라."""

def blind_prompt(batch):
    lines = "\n".join(f"{i+1}. {t}" for i, t in enumerate(batch))
    return f"""아래 한국어 문장들은 스마트 조명에 대한 사용자 요청이다. 각 문장을 읽고, 그 문장이 나타내는 것을 분류하라.

- color: red, yellow, blue, green, purple, orange, white 중 하나, 색을 말하지 않았으면 none
- emotion: sadness, happiness, anger, calm, anxiety 중 하나, 감정이 드러나지 않으면 none
- intensity: soft, strong, bright, dark 중 하나, 밝기를 말하지 않았으면 neutral

문장:
{lines}

각 문장에 대해 {{"n": 번호, "color": ..., "emotion": ..., "intensity": ...}} 형식의 객체를 만들어 JSON 배열로만 출력하라. 설명하지 마라."""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=12); ap.add_argument("--target", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--batch", type=int, default=20)
    a = ap.parse_args()
    if not KEY: sys.exit("GEMINI_API_KEY is not set")
    rng = random.Random(a.seed)
    cells = [(c, e, i) for c in [None] + list(td.COLOR_PROFILES) for e in [None] + list(td.EMOTION_PROFILES) for i in td.INTENSITY_MODIFIERS]
    print(f"[gen] {len(cells)} cells x {a.per_cell} candidates")
    def one(cell):
        c, e, i = cell
        txt = cached(f"gen|{MODEL}|{c}|{e}|{i}|{a.per_cell}|v3", lambda: gemini(gen_prompt(c, e, i, a.per_cell), 1.0))
        return cell, parse_array(txt)
    cands = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for k, (cell, texts) in enumerate(ex.map(one, cells), 1):
            c, e, i = cell
            for t in texts: cands.append({"text": t, "color": c, "emotion": e, "intensity": i})
            if k % 40 == 0: print(f"  {k}/{len(cells)} cells, {len(cands)} candidates", flush=True)
    # dedupe
    seen = set(); uniq = []
    for r in cands:
        if r["text"] in seen: continue
        seen.add(r["text"]); uniq.append(r)
    print(f"[gen] {len(cands)} candidates, {len(uniq)} unique")
    (OUT).mkdir(parents=True, exist_ok=True)
    with (OUT / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for r in uniq: f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------- blind back-labelling
    batches = [uniq[i:i + a.batch] for i in range(0, len(uniq), a.batch)]
    print(f"[verify] {len(batches)} batches of {a.batch}")
    def verify(idx_batch):
        idx, batch = idx_batch
        texts = [r["text"] for r in batch]
        raw = cached(f"blind|{MODEL}|{idx}|{hashlib.sha256(chr(10).join(texts).encode()).hexdigest()[:16]}", lambda: gemini(blind_prompt(texts), 0.0))
        out = {}
        m = re.search(r"\[.*\]", raw, re.S)
        if m:
            try:
                for o in json.loads(m.group(0)):
                    n = int(o.get("n", 0))
                    if 1 <= n <= len(batch): out[n - 1] = (o.get("color"), o.get("emotion"), o.get("intensity"))
            except Exception: pass
        return idx, out
    labels = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for k, (idx, out) in enumerate(ex.map(verify, list(enumerate(batches))), 1):
            for j, v in out.items(): labels[idx * a.batch + j] = v
            if k % 25 == 0: print(f"  {k}/{len(batches)} batches", flush=True)
    def norm(x, none_ok=("none", "None", None, "", "null")):
        return None if (x in none_ok or (isinstance(x, str) and x.lower() == "none")) else (x.lower() if isinstance(x, str) else x)
    kept, rejected = [], []
    for n, r in enumerate(uniq):
        lab = labels.get(n)
        if lab is None: r["reject"] = "no_back_label"; rejected.append(r); continue
        lc, le, li = norm(lab[0]), norm(lab[1]), (lab[2].lower() if isinstance(lab[2], str) else lab[2])
        li = "neutral" if li in (None, "none", "") else li
        if (lc, le, li) != (r["color"], r["emotion"], r["intensity"]):
            r["reject"] = f"back_label {lc}/{le}/{li}"; rejected.append(r); continue
        kept.append(r)
    print(f"[verify] kept {len(kept)} / {len(uniq)} ({100*len(kept)/max(len(uniq),1):.1f} % round-trip agreement)")

    # ---------------------------------------------------------------- leakage, gold, lexical novelty, balancing
    existing = set()
    for f in list((REPO / "backend/models/compact_llm/datasets/keff_series").rglob("*.jsonl")) + \
             list((REPO / "backend/models/compact_llm/datasets/holdout_natural").rglob("*.jsonl")):
        for l in f.open(encoding="utf-8"): existing.add(json.loads(l)["input"])
    kept = [r for r in kept if r["text"] not in existing]
    def gold(c, e, i): return td.normalize_output(td.resolve_case_output({"base_color": c, "emotion": e, "intensity": i}))
    def has_catalogue(text, c, e, i):
        hit = {}
        hit["color"] = bool(c) and any(p in text for p in td.COLOR_PROFILES[c]["phrases"])
        hit["emotion"] = bool(e) and any(p in text for p in td.EMOTION_PROFILES[e]["phrases"])
        hit["intensity"] = i != "neutral" and any(p in text for p in td.INTENSITY_MODIFIERS[i]["phrases"])
        need = [k for k, v in (("color", c), ("emotion", e), ("intensity", i if i != "neutral" else None)) if v]
        hit["all_named_attributes_use_catalogue_wording"] = bool(need) and all(hit[k] for k in need)
        hit["no_named_attribute_uses_catalogue_wording"] = bool(need) and not any(hit[k] for k in need)
        return hit
    by_cell = defaultdict(list)
    for r in kept: by_cell[(r["color"], r["emotion"], r["intensity"])].append(r)
    for v in by_cell.values(): rng.shuffle(v)
    rows, per = [], 0
    while len(rows) < a.target and any(len(v) > 0 for v in by_cell.values()):
        per += 1
        for cell in sorted(by_cell, key=lambda x: (str(x[0]), str(x[1]), x[2])):
            v = by_cell[cell]
            if len(v) >= 1 and sum(1 for r in rows if (r["base_color"], r["emotion"], r["intensity"]) == cell) < per:
                r = v.pop()
                c, e, i = cell
                src = "paraphrase_mixed" if c and e else "paraphrase_color_only" if c else "paraphrase_emotion_only" if e else "paraphrase_fallback"
                rows.append({"instruction": td.SYSTEM_PROMPT, "input": r["text"], "output": gold(c, e, i),
                             "emotion": e, "base_color": c, "intensity": i, "source": src, "lexical": has_catalogue(r["text"], c, e, i), "char_len": len(r["text"])})
                if len(rows) >= a.target: break
    rng.shuffle(rows)
    tuples = Counter(tuple(int(r["output"][k]) for k in DIMS) for r in rows)
    p = OUT / "holdout_paraphrase.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (OUT / "rejected.jsonl").open("w", encoding="utf-8") as f:
        for r in rejected: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    h = hashlib.sha256(p.read_bytes()).hexdigest(); (OUT / "holdout_paraphrase.sha256").write_text(f"{h}  {p.name}\n")
    sample = rng.sample(rows, min(60, len(rows)))
    sp = ["# 패러프레이즈 홀드아웃 저자 확인용 표본 (60행)", "",
          "생성 모델이 만든 문장과 정책이 부여한 정답이 맞는지 저자가 확인한다. 색·감정·강도 중 하나라도 문장과 어긋나면 '아니오'로 표시한다.", "",
          "| # | 문장 | 목표 색 | 목표 감정 | 목표 강도 | 정답 튜플 | 맞는가 | 메모 |", "|--:|---|---|---|---|---|---|---|"]
    for n, r in enumerate(sample, 1):
        tup = ", ".join(f"{k} {r['output'][k]}" for k in DIMS)
        sp.append(f"| {n} | {r['input']} | {r['base_color'] or '-'} | {r['emotion'] or '-'} | {r['intensity']} | {tup} |  |  |")
    (OUT / "spotcheck_sample.md").write_text("\n".join(sp) + "\n", encoding="utf-8")
    nov = Counter()
    for r in rows:
        nov["all catalogue wording"] += r["lexical"]["all_named_attributes_use_catalogue_wording"]
        nov["no catalogue wording"] += r["lexical"]["no_named_attribute_uses_catalogue_wording"]
    rep = ["# Paraphrase hold-out (K240 production policy, generated by an external LLM)", "",
           f"- generator: {MODEL} (external API); blind back-labeller: same model, separate pass, target hidden",
           f"- API calls: {_calls[0]}", f"- candidates generated: {len(uniq)} unique over {len(cells)} attribute cells",
           f"- round-trip agreement (kept / candidates): {len(kept)} / {len(uniq)} = {100*len(kept)/max(len(uniq),1):.1f} %",
           f"- rows released: {len(rows)}; reachable tuples covered {len(tuples)}/240; min rows per tuple {min(tuples.values()) if tuples else 0}, max {max(tuples.values()) if tuples else 0}",
           f"- exact-string overlap with any K-series or frame hold-out utterance: 0 (checked and removed before balancing)",
           f"- sources: {dict(Counter(r['source'] for r in rows))}",
           f"- lexical novelty: rows where every named attribute uses catalogue wording {nov[chr(39)+chr(39)] if False else nov['all catalogue wording']}; rows where no named attribute uses catalogue wording {nov['no catalogue wording']}",
           f"- utterance length (characters): min {min(r[chr(39)+chr(39)] if False else r['char_len'] for r in rows)}, median {sorted(r['char_len'] for r in rows)[len(rows)//2]}, max {max(r['char_len'] for r in rows)}",
           f"- sha256 {h}", "",
           "No human subjects are involved. The gold tuple comes from the executable policy applied to the target attribute triple;",
           "the back-labelling pass only filters candidates whose wording does not express that triple. It shares a model with the",
           "generator, so `spotcheck_sample.md` is provided for author verification."]
    (OUT / "report.md").write_text("\n".join(rep) + "\n", encoding="utf-8"); print("\n".join(rep))

if __name__ == "__main__":
    main()
