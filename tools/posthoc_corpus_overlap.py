"""Post hoc contamination screen of the pretraining corpus against the two evaluation sets built AFTER it.

The corpus was decontaminated in August 2026 against the material that existed then (development validation and
test splits, production rule benchmark); clean_corpus_report.json records that pass. The unseen-frame hold-out and
the machine-paraphrase stress set were written later, so they could not have been part of it. This script performs
the same three checks against them after the fact, so the manuscript can separate the two events.
"""
import json, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "Implement_New_Android_v6/backend/models/compact_llm/datasets/pretrain_runs/20260805_clean_v1"
SETS = {
 "unseen-frame hold-out": ROOT / "Implement_New_Android_v6/backend/models/compact_llm/datasets/holdout_natural/K240/holdout_2000.jsonl",
 "machine-paraphrase stress set": ROOT / "Implement_New_Android_v6/backend/models/compact_llm/datasets/holdout_paraphrase/K240/holdout_paraphrase.jsonl",
}
cand = [p for p in CORPUS.rglob("*.txt")] or [p for p in CORPUS.iterdir() if p.is_file()]
print("corpus dir:", CORPUS.name, "files:", [p.name for p in cand][:6])
txt = None
for p in cand:
    if p.suffix == ".txt" and p.stat().st_size > 1_000_000: txt = p; break
assert txt, cand
lines = txt.read_text(encoding="utf-8", errors="replace").splitlines()
print(f"corpus {txt.name}: {len(lines):,} lines")

def norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"\s+", "", s)
def toks(s):
    return set(re.findall(r"[0-9A-Za-z가-힣]+", unicodedata.normalize("NFKC", s).lower())) or {s}

exact_set = set(lines); norm_set = {norm(l) for l in lines}
# inverted index on tokens for the Jaccard pass
from collections import defaultdict
inv = defaultdict(list)
ctoks = []
for i, l in enumerate(lines):
    tk = toks(l); ctoks.append(tk)
    for w in tk: inv[w].append(i)

out = {}
for name, path in SETS.items():
    rows = [json.loads(x) for x in path.open(encoding="utf-8")]
    utts = [r["input"] for r in rows]
    ex = sum(1 for u in utts if u in exact_set)
    nm = sum(1 for u in utts if norm(u) in norm_set) - ex
    maxj, argmax = 0.0, None
    near = 0
    for u in utts:
        tk = toks(u); seen = set()
        for w in tk: seen.update(inv.get(w, ()))
        best = 0.0
        for i in seen:
            c = ctoks[i]; j = len(tk & c) / len(tk | c)
            if j > best: best = j
        if best >= 0.8: near += 1
        if best > maxj: maxj, argmax = best, u
    out[name] = {"rows": len(utts), "exact": ex, "normalized_only": max(nm, 0), "near_dup_ge_0.8": near, "max_jaccard": round(maxj, 4)}
    print(f"{name}: rows {len(utts)}, exact {ex}, normalized-only {max(nm,0)}, near-dup(J>=0.8) {near}, max Jaccard {maxj:.4f}")

dest = ROOT / "Implement_New_Android_v6/backend/reports/posthoc_corpus_overlap.json"
dest.write_text(json.dumps({"corpus_file": txt.name, "corpus_lines": len(lines), "checked_after_the_fact": out}, indent=1, ensure_ascii=False), encoding="utf-8")
print("written", dest)
