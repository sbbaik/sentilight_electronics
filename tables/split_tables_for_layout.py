"""Split the wide main-text tables into a compact core table and a supplementary detail table.

The submitted manuscript must not carry tables whose columns are too narrow to hold a word, so each main-text table is
reduced to the five or six columns a reader needs to follow the argument, and the seed-level values, the auxiliary
metrics (coarse, strict), the diagnostic columns and the cost columns move to a supplementary table. Nothing is
deleted: every column that leaves the main text reappears in the supplement with its own caption.

Run after tables/make_tables.py and the analysis scripts; writes the *_core.csv and the new S-numbered detail tables,
and appends their captions to tables/EXTERNAL_CAPTIONS.md.
"""
from __future__ import annotations
import csv
from pathlib import Path
HERE = Path(__file__).resolve().parent

SRC = {}          # resolved once, before anything is written, so generated files are never read back
for _t in ("T01", "T04", "T05", "T06", "T10", "T11", "T13", "T14", "T16", "T17"):
    _c = [q for q in HERE.glob(f"{_t}_*.csv") if not q.stem.endswith("_core")]
    if _c: SRC[_t] = sorted(_c)[0]
def read(tag):
    f = SRC[tag]; rows = list(csv.reader(f.open(encoding="utf-8")))
    return f, rows[0], rows[1:]
def write(name, header, rows):
    with (HERE / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
def pick(header, rows, cols):
    idx = [header.index(c) for c in cols]
    return [header[i] for i in idx], [[r[i] if i < len(r) else "" for i in idx] for r in rows]

CAPTIONS = []
def split(tag, core_name, core_cols, detail_name, detail_cols, core_cap, detail_cap, detail_src):
    f, h, rows = read(tag)
    ch, cr = pick(h, rows, core_cols); write(core_name, ch, cr)
    dh, dr = pick(h, rows, detail_cols); write(detail_name, dh, dr)
    CAPTIONS.append((core_name, core_cap, f.name)); CAPTIONS.append((detail_name, detail_cap, detail_src))

# ---------------------------------------------------------------- T01 policies: core vs diagnostics
f, h, rows = read("T01")
split("T01", "T01_policies_keff_core", ["policy", "colours", "emotions", "intensities", "lattice size", "reachable tuples K_eff"],
      "S16_policy_diagnostics", ["policy", "collisions", "hue snaps fired", "coarse-bin cells occupied", "tuples with a strict-box neighbour", "note"],
      "Policies used in the capacity series and the effective action set each one yields. Diagnostics for the same policies (collisions, hue-snap events and coarse-bin coverage) are in Table S16.",
      "Diagnostics for the policies of Table 1: tuple collisions after normalisation, hue-snap safeguard events, and coarse-bin coverage. Reported per policy.", "make_tables.py")

# ---------------------------------------------------------------- T04 K series: panel (a) fixed steps, panel (b) matched exposure
f, h, rows = read("T04")
fixed = [r for r in rows if r[0].startswith("fixed steps")]
epochs = [r for r in rows if r[0].startswith("fixed epochs")]
other = [r for r in rows if not (r[0].startswith("fixed steps") or r[0].startswith("fixed epochs"))]
cols = ["K_eff", "d=128", "d=192", "d=256", "d=384", "d=512"]
ch, cr = pick(h, fixed, cols); write("T04a_keff_fixed_steps", ch, cr)
ch2, cr2 = pick(h, epochs, cols); write("T04b_keff_matched_exposure", ch2, cr2)
dh, dr = pick(h, rows + other, [h[0], "K_eff", h[7]]); write("S17_keff_threshold_widths", dh, dr)
CAPTIONS += [("T04a_keff_fixed_steps", "K series, panel (a): fixed step budget. Exact-tuple match per policy across the tested widths, mean ± sample SD over seeds; seed counts are in Table S17.", "make_tables.py"),
             ("T04b_keff_matched_exposure", "K series, panel (b): matched exposure per action. Exact-tuple match per policy across the tested widths, mean ± sample SD over seeds; seed counts are in Table S17.", "make_tables.py"),
             ("S17_keff_threshold_widths", "K series: seed counts per cell and the smallest tested width exceeding the descriptive 60 % threshold, for both training budgets, with the log–log summary. The threshold is descriptive and was chosen after the results.", "make_tables.py")]

# ---------------------------------------------------------------- T05 depth: accuracy vs latency
split("T05", "T05_depth_series_core", ["policy", "L", "parameters", "seeds", "exact tuple %"],
      "S18_depth_auxiliary", ["policy", "L", "coarse %", "strict %", "latency ms"],
      "Depth series at d = 384 with the 24k production tokenizer, for the production policy (A = 3) and the two-attribute control (A = 2). Exact-tuple match, mean ± sample SD over the stated number of seeds. Auxiliary metrics and latency are in Table S18.",
      "Depth series, auxiliary metrics: coarse and strict match and reference-decoder latency for every row of Table 5.", "make_tables.py")

# ---------------------------------------------------------------- T06 vocabulary: performance vs tokenizer diagnostics
split("T06", "T06_vocabulary_series_core", ["tokenizer", "vocab", "parameters", "seeds", "exact tuple %"],
      "S19_tokenizer_diagnostics", ["tokenizer", "vocab", "coarse %", "test tokens/line", "byte-fragment tokens %", "test tokens < 100× in pretraining %", "pretrain bits/byte (2,400 steps)"],
      "Vocabulary series at d = 384 and L = 8. Exact-tuple match, mean ± sample SD over the stated number of seeds. Tokenizer diagnostics for the same rows are in Table S19.",
      "Tokenizer diagnostics for the rows of Table 6: tokens per test line, the share of byte-fragment tokens, and the share of test tokens seen fewer than 100 times in pretraining.", "make_tables.py")

# ---------------------------------------------------------------- T10 final models: candidates vs quantization equivalence
f, h, rows = read("T10")
cand = [r for r in rows if not r[0].startswith("quantization equivalence")]
quant = [r for r in rows if r[0].startswith("quantization equivalence")]
ch, cr = pick(h, cand, ["configuration", "seeds", "parameters", "exact tuple %", "coarse %"]); write("T10_final_models_core", ch, cr)
dh, dr = pick(h, cand, ["configuration", "strict %", "invalid JSON %", "fp32 weights MB", "latency mean / p95 ms"]); write("S20_final_models_auxiliary", dh, dr)
write("S21_quantization_equivalence", ["comparison", "seeds", "file", "mean Δ exact and interval", "TOST ±3 pp"],
      [[r[0].replace("quantization equivalence (exact, q − fp32): ", ""), r[1], r[3], r[4], r[5]] for r in quant])
CAPTIONS += [("T10_final_models_core", "Five-seed candidate configurations on the development test set. Exact-tuple match and coarse match, mean ± sample SD over five seeds. Strict match, invalid-output rate, file size and reference latency are in Table S20; the quantization equivalence tests are in Table S21.", "make_tables.py"),
             ("S20_final_models_auxiliary", "Auxiliary metrics for the candidates of Table 10: strict match, invalid-output rate, fp32 weight size and reference-decoder latency.", "make_tables.py"),
             ("S21_quantization_equivalence", "Quantization equivalence on the development test set: paired difference between the mixed 4/6/8-bit export and fp32 over five seeds, with its interval and the two one-sided tests at the prospectively specified ±3 pp margin.", "make_tables.py")]

# ---------------------------------------------------------------- T11 CPU: cost vs accuracy
split("T11", "T11_cpu_cost_core", ["model", "precision", "seeds", "file MB", "median ms", "p95 ms"],
      "S22_cpu_resources", ["model", "precision", "parameters", "load s", "RSS after load MB", "peak RSS MB", "exact % (300-prompt development subset)"],
      "CPU operating cost, one seed per row, one model per process: 4 torch threads and the same deterministic 300-prompt subset of the development test set after 20 warm-up prompts. Compare file sizes only between rows of the same precision; no quantized export of the 240-class head was produced, so its quantized size is not measured. Memory, load time and the accuracy on that subset are in Table S22.",
      "CPU benchmark, resources and subset accuracy for the rows of Table 11: parameter count, load time, resident memory after load, peak resident memory, and exact-tuple match on the 300-prompt development subset. This accuracy is not comparable with any hold-out or stress-set figure.", "make_tables.py")

# ---------------------------------------------------------------- T13 hold-out: performance vs auxiliary
split("T13", "T13_holdout_core", ["configuration", "parameters", "seeds", "hold-out exact % (mean ± SD)", "hold-out 90 % CI (hierarchical bootstrap)", "development-test exact % (mean ± SD)"],
      "S23_holdout_auxiliary", ["configuration", "drop (pp)", "hold-out coarse %", "hold-out strict %", "valid output %"],
      "Unseen-frame hold-out, five seeds per configuration: exact-tuple match as mean ± sample SD, a 90 % cluster-bootstrap interval resampling seeds then frames within family then rows, and the frozen development-test value for the same configuration. These accuracies quantify performance under a constructed distribution and are not estimates, upper bounds or lower bounds for spontaneous human utterances, which were not evaluated. Auxiliary rates are in Table S23.",
      "Unseen-frame hold-out, auxiliary rates for the rows of Table 13: the drop from the development test set, coarse and strict match, and the valid-output rate.", "make_tables.py")

# ---------------------------------------------------------------- T14 baselines: accuracy vs cost
split("T14", "T14_baselines_core", ["model", "seeds", "output formulation", "development test exact %", "unseen-frame hold-out exact %", "paraphrase stress-set exact %"],
      "S24_baseline_costs", ["model", "parameters", "model file", "CPU median latency, ms (4 threads)", "invalid outputs"],
      "Non-generative baselines and the generative CompactLM on the same fine-tuning rows and the same exact-tuple metric. Seed counts are given per row; single-seed rows are descriptive only. Costs are in Table S24.",
      "Cost of the models of Table 14: parameters, released file size, CPU median latency on four threads, and whether an out-of-schema output is possible. File sizes are comparable only between rows of the same precision.", "make_tables.py")

# ---------------------------------------------------------------- T16 stress set: core vs lexical breakdown
split("T16", "T16_stress_core", ["configuration", "seeds", "paraphrase hold-out exact % (mean ± SD)", "90 % CI (cluster bootstrap)", "coarse %", "valid output %"],
      "S25_stress_lexical_bands", ["configuration", "rows using catalogue wording for every named attribute", "partial", "rows using catalogue wording for none"],
      "Post hoc LLM-paraphrased synthetic stress set, five seeds per configuration: exact-tuple match as mean ± sample SD, a cluster-bootstrap interval over seeds then attribute cells then rows, coarse match and valid-output rate. The same external LLM was used for generation and back-labelling, so the level is not an absolute robustness measure. The lexical breakdown is in Table S25.",
      "Stress set, accuracy by lexical band: rows whose named attributes are all phrased in the policy catalogue's own words, some of them, or none. Five-seed means.", "make_tables.py")

# ---------------------------------------------------------------- T17 generative vs head: main contrast vs attributes
split("T17", "T17_generative_vs_head_core", ["evaluation set", "seeds per model", "generative exact % (mean ± SD)", "240-class head exact % (mean ± SD)", "difference (head − generative), pp", "90 % t CI"],
      "S26_generative_vs_head_detail", ["evaluation set", "seed → row bootstrap 90 % CI", "McNemar (Stouffer z, p)", "seeds favouring the head", "generative coarse %", "head coarse %", "generative valid output %", "head valid output %"],
      "Generative JSON decoding against a 240-class head on the same backbone, the same pretrained checkpoints, the same fine-tuning rows and the same five seeds, evaluated on the same rows. The paired difference across seeds with its t interval is the primary analysis. Supporting analyses and per-attribute results are in Table S26.",
      "Supporting analyses for Table 17: the seed-to-row bootstrap interval, the row-level McNemar combination (reported as agreement among seeds, not as an effect size), the number of seeds favouring the head, coarse rates recomputed with one scorer, and output validity.", "make_tables.py")

# ---------------------------------------------------------------- S12 provenance audit: too wide for a portrait page
import csv as _csv
_src = HERE / "S12_holdout_provenance_audit.csv"
if _src.exists():
    _rows = list(_csv.reader(_src.open(encoding="utf-8"))); _h, _d = _rows[0], _rows[1:]
    def _col(n): return _h.index(n)
    _ident = ["evaluation", "seed", "d", "L", "V", "parameters (recomputed)", "tokenizer dir", "hold-out rows"]
    _hash = ["evaluation", "checkpoint sha256 (16)", "tokenizer sha256 (16)", "hold-out sha256 (16)", "development-test value and frozen source", "quantization provenance"]
    write("S12a_provenance_identity", _ident, [[r[_col(c)] for c in _ident] for r in _d])
    def _short(r):
        out = []
        for c in _hash:
            v = r[_col(c)]
            out.append(v if len(v) <= 46 else v[:44] + "…")
        return out
    write("S12b_provenance_hashes", _hash, [_short(r) for r in _d])
    CAPTIONS.append(("S12a_provenance_identity", "Provenance audit of the 30 unseen-frame hold-out evaluations, part 1: seed, architecture, parameter count recounted from the weights with the tied embedding counted once, tokenizer directory and row count. Checkpoint paths are given in the released audit file rather than here.", "audit_holdout_provenance.py"))
    CAPTIONS.append(("S12b_provenance_hashes", "Provenance audit, part 2: the first 16 hexadecimal digits of the checkpoint, tokenizer and hold-out hashes, the frozen development-test source, and for each quantized export the hash of the fp32 checkpoint it was produced from. Full-length hashes and paths are in the released audit file.", "audit_holdout_provenance.py"))

cap = HERE / "EXTERNAL_CAPTIONS.md"; txt = cap.read_text(encoding="utf-8").rstrip()
have = {l.split("|")[1].strip() for l in txt.splitlines() if l.startswith("| ")}
add = [f"| {n} | {c} | {src} |" for n, c, src in CAPTIONS if n not in have]
if add: cap.write_text(txt + "\n" + "\n".join(add) + "\n", encoding="utf-8")
print(f"wrote {len(CAPTIONS)} tables; {len(add)} captions appended")
for n, c, _ in CAPTIONS: print("  ", n)
