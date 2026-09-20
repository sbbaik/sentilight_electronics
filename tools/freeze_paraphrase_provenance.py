"""Freeze the post hoc LLM-paraphrased synthetic stress set: derive the accepted list, copy the raw API responses out of
the hidden cache, write the generation provenance (model, date, temperature, verbatim prompts) and a SHA-256 manifest.

Creates nothing new and calls no API. Credentials are never written: the provenance file records the model name and the
environment variable that held the key, not the key.
"""
from __future__ import annotations
import hashlib, json, shutil, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
D = REPO / "backend/models/compact_llm/datasets/holdout_paraphrase/K240"
import importlib.util
spec = importlib.util.spec_from_file_location("bhp", REPO / "tools/build_holdout_paraphrase.py")
bhp = importlib.util.module_from_spec(spec)
sys.argv = ["x"]  # the module parses args only inside main()
spec.loader.exec_module(bhp)

def sha(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while (b := f.read(1 << 20)): h.update(b)
    return h.hexdigest()

cands = [json.loads(l) for l in (D / "candidates.jsonl").open(encoding="utf-8")]
rej = {json.loads(l)["text"] for l in (D / "rejected.jsonl").open(encoding="utf-8")}
accepted = [c for c in cands if c["text"] not in rej]
with (D / "accepted.jsonl").open("w", encoding="utf-8") as f:
    for r in accepted: f.write(json.dumps(r, ensure_ascii=False) + "\n")
released = {json.loads(l)["input"] for l in (D / "holdout_paraphrase.jsonl").open(encoding="utf-8")}

raw = D / "raw_api_responses"
if (D / ".cache").exists():
    if raw.exists(): shutil.rmtree(raw)
    shutil.copytree(D / ".cache", raw)
n_raw = len(list(raw.glob("*.json"))) if raw.exists() else 0

# verbatim prompts for one representative cell of each kind, plus the back-labelling prompt
samples = {
    "generation_mixed_colour_emotion_intensity": bhp.gen_prompt("orange", "sadness", "soft", 16),
    "generation_colour_only_neutral": bhp.gen_prompt("blue", None, "neutral", 16),
    "generation_emotion_only_intensity": bhp.gen_prompt(None, "calm", "dark", 16),
    "generation_fallback_neutral": bhp.gen_prompt(None, None, "neutral", 16),
    "blind_back_labelling": bhp.blind_prompt(["<문장 1>", "<문장 2>", "…", "<문장 20>"]),
}
(D / "prompts.json").write_text(json.dumps(samples, ensure_ascii=False, indent=1), encoding="utf-8")

prov = {
    "dataset_name": "post hoc LLM-paraphrased synthetic stress set",
    "do_not_call_it": ["natural utterance set", "human-authored set", "final untouched hold-out", "human-language validation"],
    "frozen_on": "2026-09-13", "frozen_by": "author instruction: the set is final; no regeneration, no edits, no reselection after seeing results",
    "generator": {"provider": "Google Gemini API", "model": bhp.MODEL, "endpoint": "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent",
                  "called_on": "2026-09-13 (KST)", "temperature_generation": 1.0, "temperature_back_labelling": 0.0,
                  "max_output_tokens": 4096, "total_api_calls": 432,
                  "credentials": "read from the GEMINI_API_KEY environment variable at run time; never written to any output, log, report or release"},
    "procedure": {"cells": 240, "candidates_requested_per_cell": 16,
                  "unique_candidates": len(cands), "accepted_by_blind_back_labelling": len(accepted),
                  "acceptance_rate_pct": round(100 * len(accepted) / len(cands), 1),
                  "rejected": len(rej), "released_rows": len(released),
                  "gold_source": "the executable policy applied to the target attribute triple (training_data.resolve_case_output); the model supplies wording only",
                  "back_labelling": "each candidate shown alone, target hidden, in a separate pass; kept only when the returned triple equals the target"},
    "files": {}, "raw_api_responses": n_raw,
    "caveats": ["generator and back-labeller are the same model, so acceptance is round-trip consistency, not ground truth",
                "the set measures robustness to machine-written paraphrase; it measures nothing about spontaneous human speech"],
}
for f in sorted(D.glob("*.jsonl")) + sorted(D.glob("*.json")) + [D / "report.md"]:
    if f.name == "prompts.json": continue
    prov["files"][f.name] = {"sha256": sha(f), "bytes": f.stat().st_size}
prov["files"]["prompts.json"] = {"sha256": sha(D / "prompts.json"), "bytes": (D / "prompts.json").stat().st_size}
(D / "PROVENANCE.json").write_text(json.dumps(prov, ensure_ascii=False, indent=1), encoding="utf-8")
lines = ["# Frozen manifest — post hoc LLM-paraphrased synthetic stress set", "",
         f"Frozen 2026-09-13. {len(released)} released rows; {len(cands)} unique candidates; {len(accepted)} accepted by blind back-labelling ({100*len(accepted)/len(cands):.1f} %); {len(rej)} rejected with reasons.", "",
         "| file | sha256 | bytes |", "|---|---|--:|"]
for k, v in prov["files"].items(): lines.append(f"| {k} | `{v['sha256']}` | {v['bytes']:,} |")
lines += ["", f"Raw API responses preserved: {n_raw} files in `raw_api_responses/` (generation and back-labelling replies as returned; no credentials).",
          "", "Generator: " + bhp.MODEL + ", Gemini API, called 2026-09-13 KST, temperature 1.0 for generation and 0.0 for back-labelling, 432 calls.",
          "The API key was read from an environment variable at run time and appears in no output, log, report or release file."]
(D / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:8])); print(f"\naccepted.jsonl: {len(accepted)} rows; raw responses: {n_raw}")
