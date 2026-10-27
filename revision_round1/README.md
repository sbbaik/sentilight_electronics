# Revision round 1 (record version 1.1.0)

This folder adds what the first-round revision of the article introduced. Every number that is new in the revised
manuscript is produced by a script here from the archives of the v1.0.0 record plus two checkpoint families that
v1.0.0 did not carry.

## What is new

| Path | Contents |
|---|---|
| `data/audited_requests/` | The audited request set: 240 Korean requests, one per production-policy cell in four forms (`audited_requests_K240.jsonl`, SHA-256 in `provenance.json`), the author's audit workbook with per-cell drafting hints and notes, the 16 audit notes, and the cell→gold map. Sentences were drafted by GPT-6 Astra (OpenAI, 21 October 2026) and then read, revised and annotated by the first author. Not a sample of user language. |
| `analysis/audited_eval/` | Per-row outputs and run summaries of the four model families × five seeds on the audited set (`tools/run_audited_eval.sh`). |
| `analysis/audited_requests_eval.{json,md}` | Aggregation, gate replay, paired contrasts and breakdowns (`tools/analyze_audited_requests.py`). |
| `analysis/per_action_exposure/`, `analysis/depth_pareto/`, `analysis/search_counterfactual/`, `analysis/quant_boundary/` | The four analyses added at revision, each from one script in `tools/`. |
| `figures/` | Analysis-script figures for the common-K48 test and the audited set; `figures/v51/` holds the print-size data figures 3–11 of v51 (PNG 600 dpi and PDF, `tools/make_figures_v51.py`). |
| `models/reference_W384/` | Retrained deployed architecture (d = 384, L = 8, 24k production tokenizer), fp32 weights-only, seeds 42–46 (93.5 MB each). |
| `models/head/` | Size-matched 240-class heads on the selected backbone, seeds 42–46 (`tools/compactlm_classifier_baseline.py` layout). |
| `code/` | The minimal backend subset the evaluators import (model definitions, quantized loader, scoring helpers, catalogue gate) and the three evaluators. No service configuration, no credentials. |
| `tools/` | Every script named above and `selfcontainment_test.sh`. |
| `tools/e2e/`, `analysis/e2e_simulated/` | The end-to-end software-path measurement: Tasmota emulator, measurement client, service configuration for the selected checkpoint, per-request records for both prompt configurations and the summary. Client, service and emulator ran on one host; no physical bulb. |

## Rebuilding the numbers

```bash
bash revision_round1/prepare_inputs.sh          # unpack the package archives into data/ and models/
cd revision_round1
python tools/analyze_per_action_exposure.py      # Figure 5, Table S28
python tools/analyze_depth_pareto.py             # Figure 7
python tools/analyze_search_counterfactual.py    # Section 4.1, Table S27
python tools/make_common_k48_figure.py           # Figure 4
python tools/make_quant_boundary_table.py        # Section 4.5
python tools/analyze_audited_requests.py         # Section 4.7, Tables 3–4, Figure 9, Tables S29–S31
python tools/make_figures_v51.py                 # print-size Figures 3–11 from the outputs above and the package analysis/
bash  tools/run_audited_eval.sh                  # re-runs the 20 evaluations on CPU (about 2 h); idempotent
```

`tools/selfcontainment_test.sh` performs the above in a scratch copy of the package and compares the outputs with
the released ones. Inference is CPU-only and deterministic; the per-row latencies in `analysis/audited_eval/` are
from the reference decoder path without KV cache and are not deployment figures.
