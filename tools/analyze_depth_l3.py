"""L = 3 addition to the depth series: joint analysis of D2/D3/D4 at A = 3 (K240) and A = 2 (A2K192).

Row-level McNemar per seed (seeds shared with D2/D4), Stouffer, Holm over 2 steps x 2 policies x 3 metrics,
all-seeds sign rule; seed-level means with sample SD (n-1) and t CIs; interaction (D4-D3)_A3 - (D4-D3)_A2 by
Welch on per-seed differences; TOST (+-3 pp) for D3 vs D4. Writes prereg_verdicts.md + depth_l3_analysis.json
into both report roots.
"""
from __future__ import annotations
import json, math, statistics as st
from pathlib import Path
from statistics import NormalDist
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "backend" / "reports"
DIMS = ("H", "S", "B", "Dimmer", "CT")
N = NormalDist()
POL = {"A3": {"D2": "scale_grid_depth", "D3": "scale_grid_depth_l3", "D4": "scale_grid_depth"},
       "A2": {"D2": "scale_grid_depth_a2", "D3": "scale_grid_depth_a2_l3", "D4": "scale_grid_depth_a2"}}
SEEDS_ALL = [42, 43, 44, 45, 46]
METRICS = (("strict", 0), ("coarse", 1), ("exact", 2))


def load_rows(path: Path):
    out = {}
    for line in path.open(encoding="utf-8"):
        r = json.loads(line); p, ref = r.get("predicted"), r["reference"]
        out[r["row_index"]] = (bool(r.get("strict")), bool(r.get("coarse")),
                               bool(p) and all(int(p[k]) == int(ref[k]) for k in DIMS))
    return out


def mcnemar(a, b, idx):
    keys = a.keys() & b.keys()
    bo = sum(1 for k in keys if b[k][idx] and not a[k][idx]); ao = sum(1 for k in keys if a[k][idx] and not b[k][idx])
    n, k = bo + ao, min(bo, ao)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return bo, ao, max(p, 1e-15), len(keys)


def holm(p):
    order = sorted(range(len(p)), key=lambda i: p[i]); adj = [0.0] * len(p); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i]); adj[i] = min(1.0, run)
    return adj


def tci(x, conf=0.90):
    n = len(x); m = st.mean(x); se = st.stdev(x) / math.sqrt(n); t = stats.t.ppf(0.5 + conf / 2, n - 1)
    return m, m - t * se, m + t * se


def tost(x, eq=3.0):
    n = len(x); m = st.mean(x); se = st.stdev(x) / math.sqrt(n); df = n - 1
    return max(1 - stats.t.cdf((m + eq) / se, df), stats.t.cdf((m - eq) / se, df))


def welch(a, b, conf=0.90):
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b); se = math.sqrt(va + vb)
    df = se ** 4 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); m = st.mean(a) - st.mean(b)
    t = stats.t.ppf(0.5 + conf / 2, df); p = 2 * (1 - stats.t.cdf(abs(m / se), df))
    return m, m - t * se, m + t * se, df, p


def main():
    rows = {pol: {sc: {} for sc in POL[pol]} for pol in POL}
    for pol in POL:
        for sc, root in POL[pol].items():
            for s in SEEDS_ALL:
                f = REP / root / "per_row" / f"compactlm_{sc}_f100_s{s}.jsonl"
                if f.exists(): rows[pol][sc][s] = load_rows(f)
    level = {}
    for pol in POL:
        for sc in POL[pol]:
            ex = {s: 100 * sum(v[2] for v in r.values()) / len(r) for s, r in rows[pol][sc].items()}
            vals = list(ex.values()); m, lo, hi = tci(vals)
            level[f"{pol}_{sc}"] = {"seeds": sorted(ex), "per_seed_exact": {str(k): round(v, 2) for k, v in ex.items()},
                                    "mean": m, "sd_sample": st.stdev(vals), "ci90": [lo, hi]}
    # row-level contrasts
    contrasts = []
    for pol in POL:
        for a, b in (("D2", "D3"), ("D3", "D4"), ("D2", "D4")):
            for mname, idx in METRICS:
                zs, deltas, per = [], [], {}
                for s in sorted(set(rows[pol][a]) & set(rows[pol][b])):
                    bo, ao, p, n = mcnemar(rows[pol][a][s], rows[pol][b][s], idx)
                    d = (bo - ao) / n * 100; z = -N.inv_cdf(p / 2) * (1 if d > 0 else -1 if d < 0 else 0)
                    zs.append(z); deltas.append(d); per[str(s)] = {"b_only": bo, "a_only": ao, "delta_pp": round(d, 2), "p": p}
                Z = sum(zs) / math.sqrt(len(zs)); pc = 2 * (1 - N.cdf(abs(Z)))
                contrasts.append({"policy": pol, "step": f"{a}->{b}", "metric": mname, "seeds": len(zs), "mean_delta_pp": st.mean(deltas),
                                  "stouffer_z": Z, "p": pc, "signs_consistent": all(x > 0 for x in deltas) or all(x < 0 for x in deltas), "per_seed": per})
    for c, pa in zip(contrasts, holm([c["p"] for c in contrasts])):
        c["holm_p"] = pa; c["adopted"] = pa < 0.05 and c["signs_consistent"]
    # seed-level
    seedlvl = {}
    for pol in POL:
        common = sorted(set(rows[pol]["D2"]) & set(rows[pol]["D3"]) & set(rows[pol]["D4"]))
        e = lambda sc, s: level[f"{pol}_{sc}"]["per_seed_exact"][str(s)]
        d34 = [e("D4", s) - e("D3", s) for s in common]; d23 = [e("D3", s) - e("D2", s) for s in common]; d24 = [e("D4", s) - e("D2", s) for s in common]
        m34, lo34, hi34 = tci(d34); m23, lo23, hi23 = tci(d23)
        # unpaired D4 (3 seeds) vs D3 (5 seeds)
        w = welch([e("D4", s) for s in rows[pol]["D4"]], [e("D3", s) for s in rows[pol]["D3"]])
        m24, lo24, hi24 = tci(d24)
        seedlvl[pol] = {"paired_seeds": common, "D4_minus_D2": {"per_seed": d24, "mean": m24, "ci90": [lo24, hi24]}, "D3_minus_D2": {"per_seed": d23, "mean": m23, "ci90": [lo23, hi23]},
                        "D4_minus_D3": {"per_seed": d34, "mean": m34, "ci90": [lo34, hi34], "tost_3pp_p": tost(d34)},
                        "D4_all_seeds_vs_D3_all_seeds_welch": {"diff": w[0], "ci90": [w[1], w[2]], "df": w[3], "p": w[4]}}
    ia = welch(seedlvl["A3"]["D4_minus_D3"]["per_seed"], seedlvl["A2"]["D4_minus_D3"]["per_seed"])
    ib = welch(seedlvl["A3"]["D3_minus_D2"]["per_seed"], seedlvl["A2"]["D3_minus_D2"]["per_seed"])
    inter = {"(D4-D3)_A3 - (D4-D3)_A2": {"diff": ia[0], "ci90": [ia[1], ia[2]], "df": ia[3], "p": ia[4]},
             "(D3-D2)_A3 - (D3-D2)_A2": {"diff": ib[0], "ci90": [ib[1], ib[2]], "df": ib[3], "p": ib[4]}}

    ad = {(c["policy"], c["step"]): c for c in contrasts if c["metric"] == "exact"}
    a3_34, a2_34, a3_23, a2_23 = ad[("A3", "D3->D4")], ad[("A2", "D3->D4")], ad[("A3", "D2->D3")], ad[("A2", "D2->D3")]
    p1 = a2_23["adopted"] and not a2_34["adopted"] and abs(a2_34["mean_delta_pp"]) < 3 and a3_34["adopted"] and ia[1] > 0
    p3 = not a2_34["adopted"] and not a3_34["adopted"]
    # position of D3 relative to its neighbours, per policy (pre-registered wording: "same position in both policies")
    def position(c23, c34):
        if not c23["adopted"] and abs(c23["mean_delta_pp"]) < 3: return "D2-level"
        if not c34["adopted"] and abs(c34["mean_delta_pp"]) < 3: return "D4-level"
        return "intermediate"
    pos = {"A3": position(a3_23, a3_34), "A2": position(a2_23, a2_34)}
    p2 = pos["A3"] == pos["A2"] and ia[1] <= 0 <= ia[2]
    verdict = {"P-L3-1 (L = A + 1 holds)": "supported" if p1 else "not supported",
               "P-L3-2 (depth requirement not attribute-linked)": "descriptively consistent" if p2 else "inconclusive: relative position of L = 3 differed descriptively, between-policy difference statistically inconclusive",
               "P-L3-3 (L = 3 sufficient for both)": ("supported by the adoption rule only (D4−D3 means positive, CIs include 0, TOST fails: sufficiency not established)" if p3 else "not supported")}
    out = {"d3_position": pos, "levels": level, "contrasts": contrasts, "seed_level": seedlvl, "interaction": inter, "verdicts": verdict}

    L = ["# L = 3 addition to the depth series — verdicts (A = 3 K240 and A = 2 A2K192)", "",
         "- D3 pretrain checkpoints (d 384, L 3, 24k, 2,400 steps) at seeds 42–46, shared by both policies; SFT 4 epochs; eval 2,000-row test_rule per policy (25 runs). Seed fill 2026-09-06 (config/depth_seed_fill.json, 14 runs) added seeds 45, 46 to A3 L2, A2 L2 and A2 L4, so L2/L3/L4 are on five common seeds in both policies. Three-paired-seed results are preserved in depth_l3_analysis_3paired_seeds.json.",
         "- SD below is the sample SD (n−1).", "",
         "## Exact tuple match % (per seed; mean ± SD)", "", "| Policy | L | Seeds | Per seed | Mean ± SD | 90% t CI |", "|---|--:|--:|---|--:|---|"]
    for pol in POL:
        for sc in ("D2", "D3", "D4"):
            v = level[f"{pol}_{sc}"]
            L.append(f"| {pol} | {sc[1]} | {len(v['seeds'])} | {' / '.join(f'{x:.1f}' for x in v['per_seed_exact'].values())} | {v['mean']:.1f} ± {v['sd_sample']:.1f} | [{v['ci90'][0]:.1f}, {v['ci90'][1]:.1f}] |")
    L += ["", f"## Steps (row-level McNemar per seed, Stouffer, Holm over {len(contrasts)}, all-seeds sign rule; paired seeds per policy: A3 {seedlvl['A3']['paired_seeds']}, A2 {seedlvl['A2']['paired_seeds']})", "",
          "| Policy | Step | Metric | Mean Δ pp | Stouffer z | Holm p | Signs | Adopted |", "|---|---|---|--:|--:|--:|---|---|"]
    for c in contrasts:
        L.append(f"| {c['policy']} | {c['step']} | {c['metric']} | {c['mean_delta_pp']:+.2f} | {c['stouffer_z']:+.2f} | {c['holm_p']:.2e} | {'✓' if c['signs_consistent'] else '✗'} | {'**yes**' if c['adopted'] else 'no'} |")
    L += ["", "## Seed level (exact)", ""]
    for pol in POL:
        s = seedlvl[pol]
        L.append(f"- {pol}: D4−D2 per seed {[round(x,1) for x in s['D4_minus_D2']['per_seed']]}, mean {s['D4_minus_D2']['mean']:+.2f}, 90% CI [{s['D4_minus_D2']['ci90'][0]:+.1f}, {s['D4_minus_D2']['ci90'][1]:+.1f}].")
        L.append(f"- {pol}: D3−D2 per seed {[round(x,1) for x in s['D3_minus_D2']['per_seed']]}, mean {s['D3_minus_D2']['mean']:+.2f}, 90% CI [{s['D3_minus_D2']['ci90'][0]:+.1f}, {s['D3_minus_D2']['ci90'][1]:+.1f}]; "
                 f"D4−D3 per seed {[round(x,1) for x in s['D4_minus_D3']['per_seed']]}, mean {s['D4_minus_D3']['mean']:+.2f}, 90% CI [{s['D4_minus_D3']['ci90'][0]:+.1f}, {s['D4_minus_D3']['ci90'][1]:+.1f}], TOST ±3 pp p = {s['D4_minus_D3']['tost_3pp_p']:.3f}; "
                 f"D4 ({len(rows[pol]['D4'])} seeds) − D3 ({len(rows[pol]['D3'])} seeds) Welch {s['D4_all_seeds_vs_D3_all_seeds_welch']['diff']:+.2f}, 90% CI [{s['D4_all_seeds_vs_D3_all_seeds_welch']['ci90'][0]:+.1f}, {s['D4_all_seeds_vs_D3_all_seeds_welch']['ci90'][1]:+.1f}], p = {s['D4_all_seeds_vs_D3_all_seeds_welch']['p']:.3f}.")
    L += ["", "## Interaction (Welch on per-seed differences over the paired seeds)", ""]
    for k, v in inter.items():
        L.append(f"- {k}: {v['diff']:+.2f} pp, 90% CI [{v['ci90'][0]:+.1f}, {v['ci90'][1]:+.1f}], df {v['df']:.1f}, p = {v['p']:.3f}")
    L += ["", "## Verdicts (pre-registered in `config/depth_l3_series.json`)", "", "| Prediction | Verdict |", "|---|---|"]
    L += [f"| {k} | **{v}** |" for k, v in verdict.items()]
    L += ["", f"D3 position relative to D2/D4 (exact): A3 = {pos['A3']}, A2 = {pos['A2']}.",
          "", "## Reading (five common seeds, after the seed fill)",
          "- No adjacent exact step between L = 2 and L = 4 is adopted in either policy at five seeds: every step has one dissenting seed (A3 D3→D4 and D2→D4: seed 45 D4 = 73.2 %; A2 D2→D3: seed 42; A2 D3→D4: seed 45).",
          "- Over the whole span L = 2 → 4: at A = 2 the gain is adopted (+12.6 pp, 5/5 seeds; paired-seed 90% t CI [+3.3, +22.0], 95% [+0.4, +24.8]; sensitivity: hierarchical bootstrap 95% [+5.7, +21.1], DL pooled [+4.8, +20.4]). At A = 3 a mean improvement was also observed (+4.4 pp) but one seed ran the other way (4/5) and the inference is sensitive to the interval method and confidence level (paired-seed 90% t CI [+0.2, +8.5] excludes 0, 95% t CI [−1.0, +9.7] includes it; bootstrap and DL exclude it). The primary analysis is the paired-seed difference with its t interval (five independent training replicates); bootstrap and DL are sensitivity analyses.",
          "- L = 2 could not provide consistently reliable performance across the tested policy variants: stable at A = 3 (77.3 ± 2.3) but two of five A = 2 seeds generalised poorly (65.5 %, 59.2 %) despite normal training and validation loss. Failure signature (scale_grid_depth_a2/D2_seed_instability.md): no output-mode collapse (179/158 distinct in-policy tuples of 192, zero JSON errors, out-of-policy rows 1.7/4.2 %), errors concentrated in anger and boredom (13–48 % vs 69–90 % at other seeds, whole-tuple errors) and recovered at L = 4 — suggesting seed-sensitive difficulty with the policy's emotion-conditioned tuples at L = 2, without establishing a mechanism. L = 2 is therefore not recommended as a default depth; it is not shown to be universally insufficient.",
          "- Where within L = 2..4 the gain lies is not resolved at five seeds: at A = 3 it sits mostly in L = 3 → 4 (+3.4 vs +0.9), at A = 2 mostly in L = 2 → 3 (+8.8 vs +3.9), but the (D3−D2) interaction is −7.9 pp with 90% CI [−20.9, +5.1] and the (D4−D3) interaction −0.4 pp, CI [−7.7, +6.8]. The three-seed statement 'largest gain between L = 3 and L = 4 in both policies' did not survive the seed fill.",
          "- L = A + 1 (L = 3 sufficient at A = 2): not supported by the pre-registered rule (D2→D3 at A = 2 not adopted; interaction CI includes 0). The data are compatible both with no attribute-linked shift and with a modest shift in the direction of the heuristic; neither is established.",
          "- P-L3-3: sufficiency of L = 3 was not established. The adoption rule is met only by the letter (D3→D4 not adopted in either policy). D4−D3 is +3.4 / +3.9 pp with CIs including 0 and TOST ±3 pp fails in both, so 'L = 3 sufficient' is not established; report as no reliable adjacent gain detected, not as sufficiency.",
          "- Under the 24k tokenizer and d = 384, no reliable adjacent gain was observed above L = 4 (D series, three seeds above L = 4); equivalence of L = 4 with deeper models is not established.",
          "- Caveats: two policies differing also in K_eff, factor cardinality and SFT step count (2,476 vs 3,072 at matched per-tuple exposure); one width, one tokenizer, one budget; depth effects in this range are of the same order as seed-to-seed spread."]
    for root in ("scale_grid_depth_l3", "scale_grid_depth_a2_l3"):
        (REP / root / "prereg_verdicts.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        (REP / root / "depth_l3_analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
