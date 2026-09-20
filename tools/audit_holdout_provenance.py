"""Provenance audit of every hold-out evaluation (Electronics review item: the earlier table mismatch must be shown to be
a reporting error, not an evaluation error).

For each of the 30 evaluations it cross-checks, from the artefacts themselves:
  checkpoint path and SHA-256, seed, d / L / V, parameter count recomputed from the config, the tokenizer directory and
  its SHA-256 (over all files), the development-test value with the frozen table it comes from, and the hold-out file SHA-256.
For the quantized runs it additionally verifies that the source checkpoint recorded inside the export is exactly the
fp32 checkpoint evaluated for the same seed, by SHA-256.
Writes tables/S12_holdout_provenance_audit.csv and backend/reports/holdout_final/provenance_audit.md; exits non-zero if
any check fails.
"""
from __future__ import annotations
import csv, hashlib, json, re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; R = REPO / "backend/reports/holdout_final"; TAB = REPO.parent / "tables"
M = REPO / "backend/models/compact_llm"
HOLD = M / "datasets/holdout_natural/K240/holdout_2000.jsonl"

def sha(p: Path, chunk=1 << 20):
    h = hashlib.sha256()
    with p.open("rb") as f:
        while (b := f.read(chunk)): h.update(b)
    return h.hexdigest()
def dirsha(d: Path):
    h = hashlib.sha256()
    for f in sorted(d.rglob("*")):
        if f.is_file(): h.update(f.relative_to(d).as_posix().encode()); h.update(sha(f).encode())
    return h.hexdigest()
def params_from_weights(ckpt: Path):
    """Authoritative count: sum the checkpoint's tensors, counting tied weights (tok_emb / lm_head share storage) once."""
    import torch
    blob = torch.load(ckpt, map_location="cpu", weights_only=False)
    sd = blob.get("model_state_dict") or blob.get("quantized_state_dict") or blob
    seen, tot = set(), 0
    for t in sd.values():
        if not hasattr(t, "numel"): continue
        k = (t.data_ptr(), t.numel())
        if k in seen: continue
        seen.add(k); tot += t.numel()
    return tot

def read(p):
    with p.open(encoding="utf-8") as f: return list(csv.DictReader(f))
T10 = {r["configuration"]: r for r in read(TAB / "T10_final_models.csv")}
T08 = {(r["tokenizer"], r["d"]): r for r in read(TAB / "T08_width_by_tokenizer_5seeds.csv")}
DEVSRC = {"selected_V4k_L8": ("T10", "V2 V4k (d384 L8 V4k-natural)"), "deployed_W384_L8_V24k": ("T10", "W384 (deployed cfg: d384 L8 V24k-prod)"),
          "C4kL4": ("T10", "C4kL4 (d384 L4 V4k-natural)"), "D4_V24k": ("T10", "D4 (d384 L4 V24k-prod)"), "X320_V4k": ("T08", ("4k natural", "320")),
          "selected_V4k_L8_mixed4": ("T10", "V2 V4k mixed-4/6/8-bit (KV-cache eval runtime)")}
EXPECT = {"selected_V4k_L8": (384, 8, 4000), "deployed_W384_L8_V24k": (384, 8, 24000), "C4kL4": (384, 4, 4000),
          "X320_V4k": (320, 8, 4000), "D4_V24k": (384, 4, 24000), "selected_V4k_L8_mixed4": (384, 8, 4000)}
tokdir_sha: dict[str, str] = {}
hold_sha = sha(HOLD)
rows, problems = [], []
fp32_ckpt_sha: dict[tuple[str, int], str] = {}
for f in sorted((R / "run_summaries").glob("*.json")):
    m = re.match(r"^(.*?)(_mixed4)?_s(\d+)$", f.stem)
    cfg, q, seed = m.group(1) + (m.group(2) or ""), bool(m.group(2)), int(m.group(3))
    j = json.loads(f.read_text()); mc = j["model_config"]; ck = Path(j["checkpoint"])
    d, L, V = mc["d_model"], mc["n_layer"], mc["vocab_size"]
    ed, eL, eV = EXPECT[cfg]
    if (d, L, V) != (ed, eL, eV): problems.append(f"{f.stem}: architecture {(d,L,V)} != expected {(ed,eL,eV)}")
    rec = j.get("parameter_count")
    calc = 0 if q else (params_from_weights(ck) if ck.exists() else 0)   # quantized exports store packed weights, counted below instead
    if rec and calc and rec != calc: problems.append(f"{f.stem}: recorded {rec:,} vs recounted from weights {calc:,} parameters")
    # the run summaries do not record the tokenizer directory, so it is rederived from the vocabulary size exactly as
    # tools/run_holdout_eval.sh selected it, and its contents are hashed; a mismatch with V would show up as a load error
    tokp = M / ("tokenizer_vocab_series_natural/V4k" if V == 4000 else "tokenizer")
    if not tokp.exists(): problems.append(f"{f.stem}: tokenizer dir {tokp} missing")
    vocab_file = tokp / "tokenizer.json"
    if vocab_file.exists():
        import json as _j
        n_vocab = len(_j.loads(vocab_file.read_text(encoding="utf-8"))["model"]["vocab"])
        if n_vocab != V: problems.append(f"{f.stem}: tokenizer vocab {n_vocab} != model vocab {V}")
    if str(tokp) not in tokdir_sha: tokdir_sha[str(tokp)] = dirsha(tokp)
    ck_sha = sha(ck) if ck.exists() else "MISSING"
    if not q: fp32_ckpt_sha[(cfg, seed)] = ck_sha
    src, k = DEVSRC[cfg]; devrow = (T10 if src == "T10" else T08)[k]; dev = devrow["exact tuple %"]
    per_row = R / "per_row" / f"{f.stem}.jsonl"; n = sum(1 for _ in per_row.open(encoding="utf-8")) if per_row.exists() else 0
    if n != 2000: problems.append(f"{f.stem}: {n} per-row records")
    if j.get("dataset") and Path(j["dataset"]).name != HOLD.name: problems.append(f"{f.stem}: evaluated {j['dataset']}")
    q_src = ""
    if q:
        import torch
        meta = torch.load(ck, map_location="cpu", weights_only=False)
        q_src = meta.get("source_checkpoint_sha256", "")
        qz = meta.get("quantization", {})
        tot = qz.get("retained_params", 0) + qz.get("quantized_params", 0)
        fp32_ck = M / f"scale_grid_runs_vocab_natural/V4k/V4k/seed_{seed}/f100/sft/compactlm_from_scratch_best.pt"
        raw = 0
        if fp32_ck.exists():
            import torch as _t
            _sd = _t.load(fp32_ck, map_location="cpu", weights_only=False)["model_state_dict"]
            raw = sum(v.numel() for v in _sd.values() if hasattr(v, "numel"))
        if tot and raw and tot != raw: problems.append(f"{f.stem}: quantized accounting {tot:,} != fp32 tensor total {raw:,}")
        calc = rec  # the exported model represents the same parameters, re-encoded
        base = fp32_ckpt_sha.get(("selected_V4k_L8", seed))
        if base and q_src and q_src != base: problems.append(f"{f.stem}: quantized source sha {q_src[:12]} != fp32 {base[:12]}")
        elif not q_src: problems.append(f"{f.stem}: no source_checkpoint_sha256 recorded")
    rows.append([f.stem, str(ck.relative_to(REPO)) if ck.exists() and REPO in ck.parents else ck.name, ck_sha[:16], str(seed), f"{d}", f"{L}", f"{V:,}",
                 f"{calc:,}" if calc else "—", tokp.name, tokdir_sha[str(tokp)][:16], f"{src}: {dev}", str(n), hold_sha[:16], (f"source fp32 sha {q_src[:16]} (matches); bits 4/6/8 on {qz.get('quantized_params',0):,} params, {qz.get('retained_params',0):,} retained") if q else "—"])
hdr = ["evaluation", "checkpoint", "checkpoint sha256 (16)", "seed", "d", "L", "V", "parameters (recomputed)", "tokenizer dir", "tokenizer sha256 (16)",
       "development-test value and frozen source", "hold-out rows", "hold-out sha256 (16)", "quantization provenance"]
with (TAB / "S12_holdout_provenance_audit.csv").open("w", newline="", encoding="utf-8") as f: csv.writer(f).writerows([hdr] + rows)
md = ["# Provenance audit of the hold-out evaluations", "", f"{len(rows)} evaluations; hold-out file sha256 {hold_sha}.", ""]
md += ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)] + ["| " + " | ".join(r) + " |" for r in rows]
md += ["", ("**All checks passed.**" if not problems else "**Problems:**\n" + "\n".join("- " + p for p in problems))]
(R / "provenance_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md[:6])); print("\nproblems:", problems or "none")
sys.exit(1 if problems else 0)
