"""Generate every table of the SentiLight capacity-search paper from the repository's analysis files.

Outputs (in this directory): T##_<name>.csv and T##_<name>.md (GitHub-flavoured Markdown), plus README.md.
Main-text tables use final (five-seed where available) results; supplementary tables (S) hold the
prospectively specified predictions/verdicts and finer decompositions. Re-running regenerates everything.
"""
from __future__ import annotations

import csv
import json
import statistics as st
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "Implement_New_Android_v6"
R = REPO / "backend" / "reports"
CFG = REPO / "config"
DIMS = ("H", "S", "B", "Dimmer", "CT")
TABLES: list[tuple[str, str, str]] = []


def emit(name: str, caption: str, header: list[str], rows: list[list], source: str):
    with (HERE / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    if any("±" in str(v) for r in rows for v in r) and "sample SD" not in caption:
        caption = caption.rstrip() + (" Values are mean ± sample SD (n − 1) across seeds; n is given in the seeds column." if "seeds" in [h.lower() for h in header] else " Values are mean ± sample SD (n − 1) across seeds; seed counts are stated in the caption.")
    md = [f"**{name}.** {caption}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    md += ["", f"Source: `{source}`"]
    (HERE / f"{name}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    TABLES.append((name, caption, source)); print("wrote", name)


def table(root: str) -> list[dict]:
    return json.loads((R / root / "width_analysis.json").read_text(encoding="utf-8"))["table"]


def cell(root: str, scale: str) -> dict:
    return [t for t in table(root) if t["scale"] == scale][0]


def pm(m, s, nd=1):
    return f"{m:.{nd}f} ± {s:.{nd}f}"


def exact_from_per_row(p: Path) -> float:
    n = ok = 0
    for l in p.open(encoding="utf-8"):
        r = json.loads(l); n += 1; pr, ref = r.get("predicted"), r["reference"]
        ok += bool(pr) and all(int(pr[k]) == int(ref[k]) for k in DIMS)
    return 100 * ok / n


# T01 Policies and effective action spaces
def t01():
    chk = json.loads((R / "keff_policies" / "keff_policy_check.json").read_text(encoding="utf-8"))
    diag = json.loads((R / "keff_policies" / "keff_policy_diagnostics.json").read_text(encoding="utf-8"))
    pol = json.loads((CFG / "keff_policies.json").read_text(encoding="utf-8"))["policies"]
    rows = []
    for n in ("K48", "K240", "K480", "K960"):
        p = pol[n]; c = chk["policies"][n]; d = diag[n]
        rows.append([n, len(p["colors"]), len(p["emotions"]), len(p["intensities"]), c["lattice"], c["reachable"], len(c["collisions"]), c["hue_snaps"], d["coarse_cells"], d["tuples_with_strict_neighbor"], "production policy" if n == "K240" else "nested extension"])
    emit("T01_policies_keff", "Nested lighting policies and their effective action spaces. Lattice = (colours+1)(emotions+1)×intensities; reachable = distinct actuator tuples produced by running the policy over the lattice.",
         ["policy", "colours", "emotions", "intensities", "lattice size", "reachable tuples K_eff", "collisions", "hue snaps fired", "coarse-bin cells occupied", "tuples with a strict-box neighbour", "note"], rows, "backend/reports/keff_policies/keff_policy_check.json; keff_policy_diagnostics.json")


# T02 A-priori capacity prior for K_eff = 240 (the recipe's inputs and the band it produced)
def t02():
    rows = [["effective action space K_eff", "240", "enumerated from the executable policy: (7+1)(5+1)×5, 0 collisions"],
            ["attributes read by the policy A", "3", "colour, emotion, intensity"],
            ["nominal actuator space", "≈1.3×10^11", "|H|·|S|·|B|·|D|·|CT| = 361·101·101·101·348; not used for sizing"],
            ["width prior", "d ≈ 256–384 (search starting region); band computed over d 256–512", "d near K_eff, rounded to multiples of 64 (a search starting region, not a bound); the band below deliberately extends one step above the region"],
            ["depth prior", "L ≈ 6–12 (original heuristic); L = 4 adopted after the depth series", "one to two layers per attribute was the original heuristic; its direct test (L = 3 at A = 2 and A = 3, five seeds) found no support, and where the L = 2 → 4 gain lies is unresolved (interactions imprecise); depth in this range is a seed-sensitive effect to be swept with ≥ 5 seeds"],
            ["vocabulary", "V = 24k (original); 4k natural-corpus (revised by the vocabulary series)", "input-side choice; embedding term V·d"],
            ["parameter band N ≈ V·d + 12·L·d²", "≈1×10^7 – 6×10^7", "minimum V 20k, d 256, L 6 → 9.8M; maximum V 50k, d 512, L 12 → 63M. With the narrower width region d 256–384 and V 24k the band would be 10.9M–30.5M"],
            ["deployed configuration", "23.4M (d 384, L 8, V 24k)", "inside the band"],
            ["selected configuration", "15.7M (d 384, L 8, V 4k natural)", "inside the band; chosen by the series experiments"]]
    emit("T02_capacity_prior_inputs", "Inputs used to set the initial candidate ranges for SentiLight. For SentiLight, action-set enumeration and the initial structural heuristics motivated the candidate ranges subsequently tested; substituting those ranges into N ≈ V·d + 12·L·d² gives the initial band. The band is six-fold wide, so membership of the deployed model is not a validation; the validation is the series experiments, and the starting point is not offered as a numerical rule for other tasks.",
         ["quantity", "value", "how obtained"], rows, "config/keff_policies.json; paper Section 3")


# T03 Width series (24k)
def t03():
    rows = []
    for r in sorted(table("scale_grid_width"), key=lambda x: x["d_model"]):
        rows.append([r["d_model"], f"{r['params']:,}", len(r["seeds"]), pm(r["exact_mean"], r["exact_sd"]), pm(r["coarse_mean"], r["coarse_sd"]), pm(r["strict_mean"], r["strict_sd"]), f"{r['latency_ms']:.0f}"])
    emit("T03_width_series_24k", "Width series with the production 24k tokenizer (L = 8, SFT on K240 policy data, 2,000-row test). Mean ± SD over seeds; latency is the KV-cache-free 96-step reference decoder.",
         ["d", "parameters", "seeds", "exact tuple %", "coarse %", "strict %", "latency ms"], rows, "backend/reports/scale_grid_width/width_analysis.json")


# T04 K_eff series
def t04():
    fs = json.loads((R / "scale_grid_keff_fs" / "keff_analysis.json").read_text(encoding="utf-8"))
    fe = json.loads((R / "scale_grid_keff" / "keff_analysis_fixed_epochs.json").read_text(encoding="utf-8"))
    rows = []
    for cond, res in (("fixed steps (≈3,100)", fs), ("fixed epochs (4)", fe)):
        for k in ("48", "240", "480", "960"):
            by = {t["d_model"]: t for t in res["columns"][k]["table"]}
            rows.append([cond, k] + [pm(by[d]["exact_mean"], by[d]["exact_sd"]) if d in by else "" for d in (128, 192, 256, 384, 512)] + [res["absolute_knees"][k]["60"] if cond.startswith("fixed steps") else ""])
    sl = fs["absolute_slopes"]
    rows.append(["fixed steps: log d* vs log K_eff slope", "", "", "", "", "", "", f"50%: {sl['50']['slope']:.2f}; 60%: {sl['60']['slope']:.2f} (R² {sl['60']['r2']:.2f}); 70%: {sl['70']['slope']:.2f}"])
    emit("T04_keff_series", "K_eff series: exact tuple match for four nested policies across width under two SFT budgets, and the smallest tested d reaching 60 % exact under fixed steps. Seed tiers: the K240 column and the decision cells (fixed steps: K48 d128/192, K480 d192/256, K960 d256/384; matched exposure: K480 and K960 at d384/512) are five-seed cells; all other cells are three-seed screening cells. The 60 % threshold was not specified in advance; it is a descriptive common threshold chosen after the results because all four policies crossed it within the tested width grid (50 % and 70 % in the last row as sensitivity). Each K_eff level is represented by one nested policy, so action-set cardinality is partially confounded with the semantic composition of the added actions.",
         ["condition", "K_eff", "d=128", "d=192", "d=256", "d=384", "d=512", "smallest d ≥ 60 % exact"], rows, "backend/reports/scale_grid_keff_fs/keff_analysis.json; scale_grid_keff/keff_analysis_fixed_epochs.json")


# T05 Depth series
def t05():
    def rows_for(label, roots):
        t = sorted([r for root in roots for r in table(root)], key=lambda x: x["d_model"])
        return [[label, r["d_model"], f"{r['params']:,}", len(r["seeds"]), pm(r["exact_mean"], r["exact_sd"]), pm(r["coarse_mean"], r["coarse_sd"]), pm(r["strict_mean"], r["strict_sd"]), f"{r['latency_ms']:.0f}"] for r in t]
    rows = rows_for("A=3, K_eff 240 (production)", ["scale_grid_depth", "scale_grid_depth_l3"]) + rows_for("A=2, K_eff 192 (control)", ["scale_grid_depth_a2", "scale_grid_depth_a2_l3"])
    emit("T05_depth_series", "Depth series (d = 384, V = 24k production tokenizer) for the production policy (A = 3) and the attribute-count control policy (A = 2, intensity fixed neutral, K_eff 192). L = 2, 3, 4 are on five common seeds (42–46) in both policies; L ≥ 6 on three. L = 2 could not provide consistently reliable performance across the two policy variants: L = 2 → 4 is +12.6 pp at A = 2 (5/5 seeds; 90 % t CI [+3.3, +22.0], hierarchical-bootstrap 95 % CI [+5.7, +21.1]) and +4.4 pp at A = 3 (4/5; 90 % CI [+0.2, +8.5]), with two A = 2 seeds at L = 2 generalising poorly (65.5 %, 59.2 %). Whether the gain arises between L = 2 and 3 or between 3 and 4 was not resolved (no single adjacent step adopted at five seeds; policy × depth interactions imprecise), so attribute count was not used as a depth-sizing rule. Under this tokenizer and width no reliable adjacent gain was detected above L = 4, although equivalence among deeper configurations was not established. L = 8 at A = 3 is bit-identical to W384 (five seeds 80.8 ± 3.6). Absolute levels are not comparable across policies. Values are mean ± sample SD (n − 1) across seeds; n is given in the seeds column.",
         ["policy", "L", "parameters", "seeds", "exact tuple %", "coarse %", "strict %", "latency ms"], rows, "backend/reports/scale_grid_depth{,_l3}/width_analysis.json; scale_grid_depth_a2{,_l3}/width_analysis.json")


# T06 Vocabulary series with tokenizer diagnostics
def t06():
    build2 = json.loads((R / "scale_grid_vocab_natural" / "vocab_series_build.json").read_text(encoding="utf-8"))["tokenizers"]
    freq = json.loads((R / "scale_grid_vocab_natural" / "test_token_frequency_diagnostic.json").read_text(encoding="utf-8"))
    bpb = json.loads((R / "scale_grid_vocab_natural" / "bits_per_byte.json").read_text(encoding="utf-8"))["runs"]
    rows = []
    for v in ("V4k", "V8k", "V16k", "V24k"):
        r2 = table(f"scale_grid_vocab_natural/{v}")[0]; r1 = table(f"scale_grid_vocab/{v}")[0]; b = build2[v]["robustness"]
        rows.append(["natural-corpus (V2)", build2[v]["vocab_size"], f"{r2['params']:,}", len(r2["seeds"]), pm(r2["exact_mean"], r2["exact_sd"]), pm(r2["coarse_mean"], r2["coarse_sd"]),
                     b["test_tokens_per_line"], f"{100*b['test_fragment_share']:.1f}", f"{100*freq['V2 '+v]['test_lt100']:.1f}", f"{bpb['V2 '+v]['bits_per_byte']:.3f}" if ('V2 '+v) in bpb else ""])
        rows.append(["template-corpus (V1, negative control)", r1["params"] and build2[v]["vocab_size"], f"{r1['params']:,}", len(r1["seeds"]), pm(r1["exact_mean"], r1["exact_sd"]), pm(r1["coarse_mean"], r1["coarse_sd"]), "", "", f"{100*freq['V1 '+v]['test_lt100']:.1f}", ""])
    prod = cell("scale_grid_width", "W384"); bo = build2["V24k-orig"]["robustness"]
    rows.append(["production 24k (reference)", 24000, f"{prod['params']:,}", len(prod["seeds"]), pm(prod["exact_mean"], prod["exact_sd"]), pm(prod["coarse_mean"], prod["coarse_sd"]), bo["test_tokens_per_line"], f"{100*bo['test_fragment_share']:.1f}", f"{100*freq['orig24k']['test_lt100']:.1f}", f"{bpb['orig24k (W384)']['bits_per_byte']:.3f}"])
    emit("T06_vocabulary_series", "Vocabulary series (d = 384, L = 8) with tokenizer diagnostics on the 2,000 test inputs: tokens per line, share of byte-fragment tokens, share of tokens seen < 100 times in pretraining, and pretraining validation loss in bits per byte (comparable across tokenizers; per-token losses are not).",
         ["tokenizer", "vocab", "parameters", "seeds", "exact tuple %", "coarse %", "test tokens/line", "byte-fragment tokens %", "test tokens < 100× in pretraining %", "pretrain bits/byte (2,400 steps)"], rows,
         "backend/reports/scale_grid_vocab_natural/*, scale_grid_vocab/*, test_token_frequency_diagnostic.json, bits_per_byte.json")


# T07 Budget robustness
def t07():
    rows = []
    for v, a, b in (("4k natural", "scale_grid_vocab_natural/V4k", "scale_grid_budget/B4k"), ("24k natural", "scale_grid_vocab_natural/V24k", "scale_grid_budget/B24k")):
        ra, rb = table(a)[0], table(b)[0]
        rows.append([v, pm(ra["exact_mean"], ra["exact_sd"]), pm(rb["exact_mean"], rb["exact_sd"]), f"{rb['exact_mean']-ra['exact_mean']:+.1f}", pm(ra["coarse_mean"], ra["coarse_sd"]), pm(rb["coarse_mean"], rb["coarse_sd"])])
    rows.append(["gap 4k − 24k", "+18.6", "+15.3", "", "", ""])
    emit("T07_budget_robustness", "Pretraining budget doubled from 2,400 to 4,800 steps for the 4k and 24k natural-corpus tokenizers (d = 384, L = 8, three seeds). The corpus is repeated, not enlarged.",
         ["tokenizer", "exact % @2,400", "exact % @4,800", "Δ exact pp", "coarse % @2,400", "coarse % @4,800"], rows, "backend/reports/scale_grid_budget/*; scale_grid_vocab_natural/*")


# T08 Width under the 4k tokenizer and the factorial at five seeds, with seed-level statistics
def t08():
    x = {r["d_model"]: r for r in table("scale_grid_width_v4k")}; v384 = cell("scale_grid_vocab_natural/V4k", "V4k"); w = {r["d_model"]: r for r in table("scale_grid_width")}
    rows = []
    for d in (224, 256, 320):
        r = x[d]; rows.append(["4k natural", d, f"{r['params']:,}", len(r["seeds"]), pm(r["exact_mean"], r["exact_sd"]), pm(r["coarse_mean"], r["coarse_sd"]), ", ".join(f"{v['exact']:.1f}" for v in r["per_seed"].values())])
    rows.append(["4k natural", 384, f"{v384['params']:,}", len(v384["seeds"]), pm(v384["exact_mean"], v384["exact_sd"]), pm(v384["coarse_mean"], v384["coarse_sd"]), ", ".join(f"{v['exact']:.1f}" for v in v384["per_seed"].values())])
    for d in (192, 224, 256, 384):
        r = w[d]; rows.append(["24k production", d, f"{r['params']:,}", len(r["seeds"]), pm(r["exact_mean"], r["exact_sd"]), pm(r["coarse_mean"], r["coarse_sd"]), ", ".join(f"{v['exact']:.1f}" for v in r["per_seed"].values())])
    emit("T08_width_by_tokenizer_5seeds", "Width under the two tokenizer configurations at five seeds (L = 8). The 256 → 384 step is +2.8 pp under the 24k tokenizer and +10.6 pp under the 4k tokenizer.",
         ["tokenizer", "d", "parameters", "seeds", "exact tuple %", "coarse %", "per-seed exact %"], rows, "backend/reports/scale_grid_width_v4k/*, scale_grid_width/*, scale_grid_vocab_natural/V4k/*")


# T09 Seed-level contrasts (main comparisons)
def t09():
    s1 = json.loads((R / "scale_grid_combo" / "seed_level_stats.json").read_text(encoding="utf-8"))
    s2 = json.loads((R / "scale_grid_width_v4k" / "seed_level_stats.json").read_text(encoding="utf-8"))
    sens = json.loads((R / "scale_grid_width_v4k" / "interaction_sensitivity.json").read_text(encoding="utf-8"))
    rows = []
    for name, lab in (("W384->V2V4k", "deployed cfg → selected (d384 L8: V24k → V4k)"), ("W384->D4", "deployed cfg → d384 L4 V24k"), ("W384->C4kL4", "deployed cfg → d384 L4 V4k"), ("V2V4k->C4kL4", "selected → d384 L4 V4k")):
        e = s1[name]["exact"]
        rows.append([lab, f"{e['mean']:+.2f}", f"{e['sd']:.2f}", f"[{e['ci90_t'][0]:+.1f}, {e['ci90_t'][1]:+.1f}]", f"[{e['ci95_hier_bootstrap'][0]:+.1f}, {e['ci95_hier_bootstrap'][1]:+.1f}]", f"{e['seeds_positive']}/5"])
    for name, lab in (("X256->V4k384", "d256 → d384 (both V4k)"), ("X320->V4k384", "d320 → d384 (both V4k)"), ("X224->X256", "d224 → d256 (both V4k)")):
        e = s2[name]["exact"]
        rows.append([lab, f"{e['mean']:+.2f}", f"{e['sd']:.2f}", f"[{e['ci90_t'][0]:+.1f}, {e['ci90_t'][1]:+.1f}]", f"[{e['ci95_hier_bootstrap'][0]:+.1f}, {e['ci95_hier_bootstrap'][1]:+.1f}]", f"{e['seeds_positive']}/5"])
    ui = sens["unpaired_interaction"]
    rows.append(["tokenizer-configuration × width interaction (V4k384−X256) − (W384−W256)", f"{ui['estimate']:+.2f}", "", "paired [−1.9, +17.5]; unpaired Welch " + f"[{ui['ci90'][0]:+.1f}, {ui['ci90'][1]:+.1f}]", f"permutation p = {sens['permutation_p']:.3f}", "4/5"])
    emit("T09_seed_level_contrasts", "Seed-level statistics for the main paired contrasts (exact tuple match, five seeds): mean and SD of per-seed differences, 90 % t confidence interval (df = 4), hierarchical bootstrap 95 % interval (seeds, then rows), and the number of seeds with a positive difference. The prospectively specified all-seeds direction rule is met only when the last column reads 5/5.",
         ["contrast", "mean Δ pp", "SD", "90 % CI (seed t)", "95 % CI (hierarchical bootstrap) / sensitivity", "seeds > 0"], rows, "backend/reports/scale_grid_combo/seed_level_stats.json; scale_grid_width_v4k/seed_level_stats.json; interaction_sensitivity.json")


# T10 Final model table with quantization
def t10():
    fm = json.loads((R / "scale_grid_combo" / "final_model_table.json").read_text(encoding="utf-8"))["rows"]
    q1 = json.loads((R / "scale_grid_vocab_natural_q4" / "quant_equivalence.json").read_text(encoding="utf-8"))["metrics"]["exact"]
    q2 = json.loads((R / "scale_grid_combo_q4" / "quant_equivalence.json").read_text(encoding="utf-8"))["metrics"]["exact"]
    rows = []
    for r in fm:
        fam = r["family"]; ref = fm[0]["latency_mean_ms"]
        rows.append([fam, r["n_seeds"], f"{r['params']:,}", f"{r['fp32_weights_mb']:.1f}", pm(r["exact_mean"], r["exact_sd"]), pm(r["coarse_mean"], r["coarse_sd"]), pm(r["strict_mean"], r["strict_sd"]), f"{r['invalid_json_pct']:.2f}", f"{r['latency_mean_ms']:.0f} / {r['latency_p95_ms']:.0f}"])
    rows.append(["quantization equivalence (exact, q − fp32): selected model", 5, "", "17.1 MB mixed-bit file", f"{q1['mean_delta_pp']:+.2f} pp, 90 % CI [{q1['ci90_seed_t'][0]:+.2f}, {q1['ci90_seed_t'][1]:+.2f}]", "TOST ±3 pp: " + q1["tost"], "", "", ""])
    rows.append(["quantization equivalence (exact, q − fp32): d384 L4 V4k", 5, "", "12.3 MB mixed-bit file", f"{q2['mean_delta_pp']:+.2f} pp, 90 % CI [{q2['ci90_seed_t'][0]:+.2f}, {q2['ci90_seed_t'][1]:+.2f}]", "TOST ±3 pp: " + q2["tost"], "", "", ""])
    emit("T10_final_models", "Candidate configurations at five seeds and their mixed 4/6/8-bit quantized versions. Latency = KV-cache-free 96-step reference decoder (GPU); quantized rows were evaluated with the load-time-dequantizing KV-cache runtime, so their latency is not a quantization speed-up.",
         ["configuration", "seeds", "parameters", "fp32 weights MB", "exact tuple %", "coarse %", "strict %", "invalid JSON %", "latency mean / p95 ms"], rows, "backend/reports/scale_grid_combo/final_model_table.json; scale_grid_vocab_natural_q4/quant_equivalence.json; scale_grid_combo_q4/quant_equivalence.json")


# T11 CPU deployment benchmark
def t11():
    order = [("prod_fp32_23M", "deployed 23.4M (production lineage)", "generative JSON", "fp32", "23,378,304"),
             ("prod_mixed4_23M", "deployed 23.4M (production lineage)", "generative JSON", "mixed 4/6/8-bit", "23,378,304"),
             ("W384_fp32_s42", "d384 L8 V24k", "generative JSON", "fp32", "23,378,304"),
             ("W384_mixed4_s42", "d384 L8 V24k", "generative JSON", "mixed 4/6/8-bit", "23,378,304"),
             ("V4k_fp32_s42", "d384 L8 V4k (selected)", "generative JSON", "fp32", "15,698,304"),
             ("V4k_mixed4_s42", "d384 L8 V4k (selected)", "generative JSON", "mixed 4/6/8-bit", "15,698,304"),
             ("C4kL4_mixed4_s42", "d384 L4 V4k", "generative JSON", "mixed 4/6/8-bit", "8,617,344"),
             ("classifier_240class_s42", "d384 L8 V4k backbone + 240-class head", "240-class", "fp32 (no quantized export: not measured)", "15,790,704")]
    rows = []
    for n, lab, form, prec, npar in order:
        d = json.loads((R / "deploy_benchmark_t4" / f"{n}.json").read_text(encoding="utf-8")); l = d["latency_ms"]
        size = {"W384_fp32_s42": 93.5, "V4k_fp32_s42": 62.8}.get(n, d["checkpoint_mb"])
        med = f"{l['median']:.0f}" if l["median"] >= 10 else f"{l['median']:.1f}"
        p95 = f"{l['p95']:.0f}" if l["p95"] >= 10 else f"{l['p95']:.1f}"
        rows.append([lab, form, prec, npar, "1", f"{size:.1f}", f"{d['load_time_s']:.2f}", f"{d['rss_after_load_mb']:.0f}", f"{d['peak_rss_mb']:.0f}", med, p95, f"{100*d['invalid_json_rate']:.1f}", f"{100*d['exact_rate']:.1f}"])
    emit("T11_cpu_deployment_benchmark", "CPU deployment benchmark, one seed per row, one model per process on a shared Intel Core Ultra 9 285K workstation: 4 torch threads and the same deterministic 300-prompt subset of the development test set after 20 warm-up prompts. Generative rows run through the production runtime with load-time dequantization and KV-cache greedy decoding; the last row is the 240-class head under the identical protocol, and it cannot emit an out-of-schema output. fp32 sizes are weights only. Compare file sizes only between rows of the same precision: no quantized export of the 240-class head was produced, so its quantized size is not measured. Accuracy is on the 300-prompt development subset and is not comparable to any hold-out or stress-set figure.",
         ["model", "output formulation", "precision", "parameters", "seeds", "file MB", "load s", "RSS after load MB", "peak RSS MB", "median ms", "p95 ms", "invalid JSON %", "exact % (300-prompt development subset)"], rows, "backend/reports/deploy_benchmark_t4/*.json")


# T12 Human evaluation summary
def t12():
    z = zipfile.ZipFile(REPO / "documents" / "SentiLight_설문_결과정리_v3_IRBfree.xlsx"); ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    ss = ["".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml")).find("m:sheetData", ns)
    cols = [("B", "C", "D"), ("F", "G", "H"), ("J", "K", "L"), ("N", "O", "P"), ("R", "S", "T")]; Y = {}
    for row in sheet:
        vals = {}
        for c in row.findall("m:c", ns):
            v = c.find("m:v", ns)
            if v is None: continue
            col = "".join(ch for ch in c.get("r") if ch.isalpha()); vals[col] = ss[int(v.text)] if c.get("t") == "s" else v.text
        a = vals.get("A")
        if a and a.isdigit():
            for b, trio in enumerate(cols):
                for t, cc in enumerate(trio): Y[(int(a), b, t)] = float(vals[cc])
    P = sorted({k[0] for k in Y}); g = st.mean(Y.values())
    def mo(idx, val): return st.mean(v for k, v in Y.items() if k[idx] == val)
    bulbs = ["1 Gemini API", "2 Qwen3-0.6B", "3 SBERT", "4 CompactLM fp32", "5 CompactLM Q4"]
    rows = [[f"condition {bulbs[b]}", f"{mo(1,b):.2f}", f"{st.mean(Y[(p,b,0)] for p in P):.2f}", f"{st.mean(Y[(p,b,1)] for p in P):.2f}", f"{st.mean(Y[(p,b,2)] for p in P):.2f}"] for b in range(5)]
    rows.append(["all conditions", f"{g:.2f}", f"{mo(2,0):.2f}", f"{mo(2,1):.2f}", f"{mo(2,2):.2f}"])
    rows.append(["share of ratings ≥ 5", f"{100*sum(1 for v in Y.values() if v>=5)/len(Y):.0f}%", f"{100*sum(1 for k,v in Y.items() if k[2]==0 and v>=5)/(len(P)*5):.0f}%", f"{100*sum(1 for k,v in Y.items() if k[2]==1 and v>=5)/(len(P)*5):.0f}%", f"{100*sum(1 for k,v in Y.items() if k[2]==2 and v>=5)/(len(P)*5):.0f}%"])
    ssp = 15 * sum((mo(0, p) - g) ** 2 for p in P); ssb = 60 * sum((mo(1, b) - g) ** 2 for b in range(5)); sst = 100 * sum((mo(2, t) - g) ** 2 for t in range(3)); tot = sum((v - g) ** 2 for v in Y.values())
    rows.append(["variance share: participant / condition / trial / residual", f"{100*ssp/tot:.1f} / {100*ssb/tot:.1f} / {100*sst/tot:.1f} / {100*(tot-ssp-ssb-sst)/tot:.1f} %", "", "", ""])
    emit("T12_human_evaluation", "Exploratory anonymous human evaluation on the physical five-bulb path (20 participants × 5 lighting conditions × 3 trials, 0–10 scale; independent units are the 20 participants). Bulb–model mapping was fixed and trial order not counterbalanced; utterance–output pairs were not retained. The study assesses acceptability of the implemented interaction, not model preference or the final model.",
         ["quantity", "all trials", "trial 1", "trial 2", "trial 3"], rows, "documents/SentiLight_설문_결과정리_v3_IRBfree.xlsx (anonymous ratings only)")


# S1 Preregistered predictions and verdicts (supplementary)
def s1():
    rows = [
        ["W (width, 24k)", "P-W1", "coarse rises steeply W128→W256; largest step at W224→W256", "met at five seeds (W192 = W224 = 70.6; W224→W256 +7.4 pp adopted)", "scale_grid_width/prereg_verdicts.md; scale_grid_combo/five_seed_verdicts.md"],
        ["W", "P-W2", "above W256 every step gains less than W224→W256", "met", "scale_grid_width/prereg_verdicts.md"],
        ["W", "P-W3", "W384 ≥ IoTJ Gen-Policy 23M", "met (plausibility check)", "scale_grid_width/prereg_verdicts.md"],
        ["K (K_eff)", "P1 (pre-registered rule)", "8M→23M and 23M→60M both < 3.5 pp ⇒ saturation", "not used; replaced by d* vs K_eff analysis: slope 0.23–0.35 under fixed steps, ≈0 under fixed epochs", "scale_grid_keff_fs/keff_verdicts.md"],
        ["D (depth)", "P-D1", "D2→D4 and D4→D6 adopted rises", "half met (D2→D4 only; peak at L = 4)", "scale_grid_depth/prereg_verdicts.md"],
        ["D", "P-D2", "no adopted gain above D8", "met", "scale_grid_depth/prereg_verdicts.md"],
        ["D", "P-D3", "D8 reproduces W384 within 3 pp", "met exactly (bit-identical)", "scale_grid_depth/prereg_verdicts.md"],
        ["V (vocabulary, natural)", "P-V1", "flat from V8k to V24k", "rejected (monotone decline)", "scale_grid_vocab_natural/prereg_verdicts.md"],
        ["V", "P-V2", "V4k not worse than V8k", "met and inverted (V4k better)", "scale_grid_vocab_natural/prereg_verdicts.md"],
        ["V", "P-V3", "retrained V24k ≥ production 24k", "rejected (−10.9 pp)", "scale_grid_vocab_natural/prereg_verdicts.md"],
        ["V", "P-V4", "natural-corpus tokenizer beats template-corpus tokenizer at every size", "met", "scale_grid_vocab_natural/prereg_verdicts.md"],
        ["C (d384 L4 V4k)", "P-C1", "within 3 pp of d384 L8 V4k", "met at three seeds; at five seeds −4.6 pp (4/5 seeds), not equivalent", "scale_grid_combo/prereg_verdicts.md; five_seed_verdicts.md"],
        ["C", "P-C2", "latency ≈ half of L8", "met", "scale_grid_combo/prereg_verdicts.md"],
        ["C", "P-C3", "depth and vocabulary effects additive", "rejected", "scale_grid_combo/prereg_verdicts.md"],
        ["B (budget)", "P-B1", "24k gains ≥ 3 pp more than 4k from doubling steps", "met narrowly (gain itself seed-split)", "scale_grid_budget/prereg_verdicts.md"],
        ["B", "P-B2", "4k still > 24k by > 5 pp at 4,800 steps", "met (+15.3 pp, all seeds)", "scale_grid_budget/prereg_verdicts.md"],
        ["X (width under V4k)", "P-X1", "d256/V4k within 3 pp of d384/V4k; d224→d256 adopted rise", "rejected on both parts (−10.6 pp, 5/5)", "scale_grid_width_v4k/prereg_verdicts.md"],
        ["X", "P-X2", "SD at d256 ≤ 2× SD at d384", "rejected (4.4 vs 1.6)", "scale_grid_width_v4k/prereg_verdicts.md"],
        ["A (attribute-count control)", "P-A1", "at A = 2 the shallowest depth within 3 pp of L = 8 is L = 2", "rejected as written (D2 → D4 +6.3 pp adopted); note: P-A1 mis-operationalised L = A + 1, which predicts L = 3, so this alone does not reject the heuristic", "scale_grid_depth_a2/prereg_verdicts.md"],
        ["A", "P-A2", "D2 → D4 rise at A = 2 of similar size to A = 3 and adopted", "descriptively consistent (+6.3 vs +6.5 pp; difference −0.2 pp, 90 % CI [−5.7, +5.3]); shape above L = 4 not identical", "scale_grid_depth_a2/prereg_verdicts.md"],
        ["A-L3 (direct test of L = A + 1)", "P-L3-1", "at A = 2, L = 3 reaches the L = 4 level (D2→D3 adopted, D3→D4 not); at A = 3 D3→D4 adopted; interaction CI excludes 0", "not supported by the rule at five seeds (A = 2: D2→D3 +8.8 pp, 4/5 seeds, not adopted; D3→D4 +3.9 pp, 4/5; interaction (D3−D2) −7.9 pp, 90 % CI [−20.9, +5.1]); data compatible with no shift and with a modest shift; not a rejection of a general relation", "scale_grid_depth_l3/prereg_verdicts.md"],
        ["A-L3", "P-L3-2", "D3 occupies the same position relative to D2/D4 in both policies; interaction CI includes 0", "inconclusive: the relative position of L = 3 differed descriptively (A = 3: at the L = 2 level; A = 2: intermediate) but the between-policy difference is statistically inconclusive ((D3−D2) −7.9 pp, 90 % CI [−20.9, +5.1]; (D4−D3) −0.4 pp, CI [−7.7, +6.8])", "scale_grid_depth_l3/prereg_verdicts.md"],
        ["A-L3", "P-L3-3", "D3 → D4 not adopted in either policy (L = 3 already sufficient)", "sufficiency of L = 3 not established (adoption rule met only because one seed dissents in each policy; D4−D3 +3.4 / +3.9 pp, CIs include 0, TOST ±3 pp fails)", "scale_grid_depth_l3/prereg_verdicts.md"],
    ]
    emit("S01_preregistered_predictions", "Prospectively specified predictions and their verdicts (supplementary). Predictions were written and recorded internally, with SHA-256 hashes of the inputs, before each series ran (no external time-stamped registry); rejected predictions are reported unchanged.",
         ["series", "prediction", "as written", "verdict", "record"], rows, "config/*_series.json; backend/reports/*/prereg_verdicts.md")


# S2 Error decomposition by input structure and source layer (supplementary)
def s2():
    d = json.loads((R / "scale_grid_combo" / "error_decomposition.json").read_text(encoding="utf-8"))
    rows = []
    for sec in ("By source layer", "By input structure"):
        for g, m in d[sec].items():
            rows.append([sec.replace("By ", ""), g, m["W384"]["n"] // 3, f"{m['W384']['exact']:.1f}", f"{m['V2V4k']['exact']:.1f}", f"{m['D4']['exact']:.1f}", f"{m['C4kL4']['exact']:.1f}"])
    emit("S02_error_decomposition", "Exact tuple match by test-set source layer and by input structure (whether the utterance names a colour, an emotion and a non-neutral intensity), pooled over seeds 42–44.",
         ["grouping", "group", "rows per seed", "deployed d384 L8 V24k", "selected d384 L8 V4k", "d384 L4 V24k", "d384 L4 V4k"], rows, "backend/reports/scale_grid_combo/error_decomposition.json")


# S05 K-series common-action-subset analysis
def s05():
    j = json.loads((R / "scale_grid_keff_fs" / "common_subset_analysis.json").read_text(encoding="utf-8"))
    import statistics as _st
    def f(v):
        v = [x for x in v if x is not None]
        return f"{_st.mean(v):.1f} ± {_st.stdev(v):.1f}" if len(v) > 1 else (f"{v[0]:.1f}" if v else "")
    rows = []
    for key, r in j.items():
        cond, pol, d = key.split("/")
        rows.append([cond.replace("_", " "), pol, d[1:], r.get("nseeds", len([x for x in r["all"] if x is not None])), f(r["all"]), f(r["k48"]), r["n48"], f(r["k240"]), r["n240"], f(r["new"]), r["nnew"], f(r["macro"])])
    emit("S05_keff_common_action_subset", "K series scored on common action subsets (supplementary; exact %, all available seeds: five where the seed fill applied, three otherwise; the seeds column gives n). Each model is evaluated on the rows of its own 2,000-row test set whose lattice cell (colour, emotion, intensity) belongs to the K48 catalogue, to the K240 catalogue, or lies outside K240 (actions added by the larger policies); macro = mean over reachable actions of the per-action exact rate. Under fixed steps the larger policies lose accuracy on the shared K48/K240 actions themselves, while their added actions score as high or higher, so the K_eff effect is not explained by the added actions being harder; under matched exposure the shared-action gap narrows.",
         ["SFT budget", "policy", "d", "seeds", "all rows", "K48-subset rows", "n", "K240-subset rows", "n", "rows outside K240", "n", "macro over actions"], rows, "backend/reports/scale_grid_keff_fs/common_subset_analysis.json (tools/keff_common_subset.py)")


# S06 K-series ring analysis
def s06():
    j = json.loads((R / "scale_grid_keff_fs" / "ring_analysis.json").read_text(encoding="utf-8"))
    import statistics as _st
    def f(v): return f"{_st.mean(v):.1f} ± {_st.stdev(v):.1f}" if len(v) > 1 else (f"{v[0]:.1f}" if v else "")
    rows = []
    for key, r in j.items():
        cond, pol, d = key.split("/")
        if int(d[1:]) not in (256, 384, 512) or pol == "K48": continue
        rows.append([cond.replace("_", " "), pol, d[1:], r["nseeds"], f(r.get("R48", [])), f(r.get("R240", [])), f(r.get("R480", [])), f(r.get("R960", []))])
    emit("S06_keff_ring_analysis", "K series scored by nested ring of the lattice cell (supplementary; exact %, mean ± sample SD over available seeds): R48 = K48 cells (108–473 rows depending on the policy's test set), R240 = K240 \\ K48, R480 = K480 \\ K240, R960 = K960 \\ K480. Under fixed steps the rings shared with smaller policies are answered no better, and descriptively worse, than the newly added rings; the loss from expanding the policy is therefore not confined to newly added actions. Models were evaluated on policy-specific test rows sharing the same action cells, rather than on identical utterances; cross-policy ring comparisons are therefore descriptive (Table S07 repeats the comparison on identical utterances).",
         ["SFT budget", "policy", "d", "seeds", "R48", "R240 (K240 \\ K48)", "R480 (K480 \\ K240)", "R960 (K960 \\ K480)"], rows, "backend/reports/scale_grid_keff_fs/ring_analysis.json (tools/keff_ring_analysis.py)")


# S07 K-series models on the common K48 test set
def s07():
    j = json.loads((R / "scale_grid_keff_common48" / "common48_analysis.json").read_text(encoding="utf-8"))
    rows = []
    for key, v in j["levels"].items():
        cond, pol, d = key.split("/")
        rows.append([cond.replace("_", " "), d[1:], pol, len(v["seeds"]), f"{v['mean']:.1f}" + (f" ± {v['sd']:.1f}" if v["sd"] is not None else ""), "", "", "", ""])
    for c in j["contrasts"]:
        rows.append([c["budget"].replace("_", " "), c["d"], c["contrast"], len(c["seeds"]), "", ", ".join(f"{x:+.1f}" for x in c["deltas"]), f"{c['mean']:+.1f} [{c['ci90'][0]:+.1f}, {c['ci90'][1]:+.1f}]", f"{c['holm_p']:.1e}", "yes" if c["same_sign"] else "no"])
    emit("S07_keff_common_test_set", "K-series models evaluated on one fixed test set — the K48 policy's 2,000-row test_rule, i.e. identical utterances for every model (supplementary; exact %). Upper rows: level per policy model (mean ± sample SD over available seeds). Lower rows: larger-policy model minus the K48 model trained on the same seed (common seeds 42–44), with per-seed differences, seed-level 90 % t interval, Holm-corrected Stouffer p of the row-level McNemar tests, and the all-seeds sign rule. Recomputing the 2,000 K48 references under every larger nested policy gives identical executable tuples (0/2,000 conflicts), so utterances and target actions are identical across models. Under the fixed-step budget the shared actions are answered markedly worse by the larger-policy models; under matched exposure the point-estimate gaps at d = 384 narrow (difference of differences on the same seeds: K240 +3.5 pp, 90 % CI [−2.2, +9.3]; K480 +4.0 [−8.5, +16.6]; K960 +12.4 [−2.4, +27.2]) but every three-seed interval includes zero. K48 at d = 256 is under-trained under fixed epochs (596 steps) and is not used for the budget comparison.",
         ["SFT budget", "d", "policy / contrast", "seeds", "exact % on K48 test", "per-seed Δ pp", "mean Δ [90 % CI]", "Holm p", "all seeds same sign"], rows, "backend/reports/scale_grid_keff_common48/common48_analysis.json (tools/analyze_keff_common48.py)")


# S3 Run inventory
def s3():
    inv = json.loads((R / "run_inventory_counts.json").read_text(encoding="utf-8"))
    grid = {"W width (24k)": ("d ∈ {128,192,224,256,320,384,512}, L 8", "3 (5 at 128/192/224/256/384/512)"),
            "K K_eff, matched exposure (fixed epochs)": ("K48/K480/K960 × d ∈ {128,192,256,384,512}; K240 = W series", "3 (5 at K480/K960 d384, d512)"),
            "K K_eff, fixed steps": ("K48/K480/K960 × d ∈ {128,192,256,384,512}; K240 = W series", "3 (5 at threshold cells K48 d128/192, K480 d192/256, K960 d256/384)"),
            "D depth (A = 3), incl. L = 3": ("L ∈ {2,3,4,6,8,12,16}, d 384", "3 (5 at L = 2, 3, 4)"),
            "A depth at A = 2, incl. L = 3": ("L ∈ {2,3,4,6,8}, d 384; pretrain linked from D", "3 (5 at L = 2, 3, 4)"),
            "V vocabulary, template corpus": ("V ∈ {4k,8k,16k,24k} (negative control)", "3"),
            "V vocabulary, natural corpus": ("V ∈ {4k,8k,16k,24k}", "3 (5 at 4k)"),
            "C combined": ("d 384, L 4, V 4k", "5"),
            "B budget": ("4k / 24k natural at 4,800 steps", "3"),
            "X width under V4k": ("d ∈ {224,256,320}, L 8, V 4k", "5"),
            "K common-test-set evaluations (existing checkpoints on the K48 test)": ("K48/K240/K480/K960 × d ∈ {256,384} × both budgets on the K48 test_rule", "all available")}
    rows = [[k, grid[k][0], grid[k][1], (v["pretrain"] or ("—" if v["sft"] == 0 else "linked")), v["sft"] or "—", v["eval_fp32"], v["eval_quant"] or ""] for k, v in inv["series"].items()]
    t = inv["total"]; rows.append(["total (this paper's series; IoTJ clean-grid reruns excluded)", "", "", t["pretrain"], t["sft"], t["eval_fp32"], t["eval_quant"]])
    emit("S03_run_inventory", "Run inventory (supplementary), counted from artefacts on disk with one unit per column: independent pretraining runs (2,400 steps unless stated; 'linked' = checkpoints reused from another series), SFT-trained checkpoints (one per policy × configuration × seed; SFT 4 epochs unless stated), fp32 evaluation executions (2,000 rows each) and quantized evaluation executions. Seed reinforcement added after screening is included in the per-series counts.",
         ["series", "grid", "seeds", "pretraining runs", "SFT checkpoints", "fp32 evaluations", "quantized evaluations"], rows, "backend/reports/run_inventory_counts.json (tools/keff_ring_analysis.py)")


def readme():
    lines = ["# Tables for the SentiLight capacity-search paper", "", "Generated by `make_tables.py` from `Implement_New_Android_v6/backend/reports/` (and the anonymous survey workbook). Each table ships as CSV and Markdown. T = main text, S = supplementary.", "", "| Table | Caption | Source |", "|---|---|---|"]
    for n, cap, src in TABLES: lines.append(f"| {n} | {cap} | {src} |")
    lines.insert(1, "All ± values are mean ± sample SD (n − 1) across independent training seeds; the number of seeds is given per row or in the caption. Statistical intervals are computed from the per-seed values (paired-seed t intervals as primary analysis; hierarchical bootstrap and DerSimonian–Laird pooling as sensitivity analyses).")
    (HERE / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for f in (t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, s1, s2, s05, s06, s07, s3):
        f()
    readme(); print("done", len(TABLES), "tables")

# tables produced by the analysis scripts keep their captions in EXTERNAL_CAPTIONS.md; append them so README.md stays complete
_ext = HERE / "EXTERNAL_CAPTIONS.md" if "HERE" in dir() else Path(__file__).resolve().parent / "EXTERNAL_CAPTIONS.md"
_rows = [l for l in _ext.read_text(encoding="utf-8").splitlines() if l.startswith("| ") and not l.startswith("| table ") and not l.startswith("|---")]
_readme = Path(__file__).resolve().parent / "README.md"
_txt = _readme.read_text(encoding="utf-8").rstrip()
_have = {l.split("|")[1].strip() for l in _txt.splitlines() if l.startswith("| ")}
_add = [l for l in _rows if l.split("|")[1].strip() not in _have]
if _add:
    _readme.write_text(_txt + "\n" + "\n".join(_add) + "\n", encoding="utf-8")
print(f"appended {len(_add)} external captions to README.md")
