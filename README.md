# Action-Set-Informed Design and System Implementation of a Compact Language Model for Smart-Lighting Control — data and code

Seongbok Baik (ORCID 0009-0009-4420-4084), Intelligent IoT Department, Daejeon University, Daejeon 34520, Republic of Korea.
Yong-Geun Hong (ORCID 0000-0003-2974-3820), School of AI Software, Daejeon University, Daejeon 34520, Republic of Korea.

This record accompanies the manuscript submitted to *Electronics* (MDPI). It contains what is needed to re-derive
every number, table and figure in the paper from the released evaluation outputs, and to re-run the training
series from the released configurations. All values reported as `mean ± sample SD` are taken across training
seeds; seed counts are given per cell.

## Layout

| Directory | Contents |
|---|---|
| `manuscript/` | The nine figures of the submitted manuscript at submission resolution and its five tables as CSV. The article itself is published by the journal. |
| `revision_round1/` | Added in version 1.1.0: everything the first-round revision introduced, with its own `README.md`, `prepare_inputs.sh` and `MANIFEST.sha256`. |
| `config/` | Series configurations (`*_series.json`, `keff_policies.json`, seed-fill configs): the frozen grid, seeds, budgets and the prospectively specified predictions for each series. |
| `prospective_predictions/` | SHA-256 hashes of the inputs recorded before each launch (`*.sha256`, `inputs.sha256`) and the verdict files (`prereg_verdicts.md`), including the predictions that were rejected. No external time-stamped registry was used. |
| `evaluation_outputs/` | One `tar.gz` per series with `per_row/*.jsonl` (input, reference tuple, predicted tuple, metric flags for every row) and `run_summaries/*.json`. 243 fp32 evaluations on the policies' own test sets, 56 on the common K48 test set, 10 quantized. |
| `datasets/` | Policy-only training, validation and 2,000-row test rows for K48, K240, K480, K960 and A2K192; the unseen-frame hold-out with its frame list; the machine-paraphrase stress set with its prompts, candidates, acceptances and rejections; and the decontaminated pretraining corpus with its token report. |
| `tokenizers/` | Production 24k tokenizer, the natural-corpus family (4k/8k/16k/24k) and the template-corpus family used as a negative control. |
| `models/selected_d384_L8_V4k/` | The selected 15.7 M model (d = 384, L = 8, 4k natural-corpus vocabulary): fp32 weights-only checkpoints and mixed 4/6/8-bit exports for seeds 42–46, with fine-tuning summaries. Optimizer state is removed, so an fp32 file is 62.8 MB and a mixed-bit file 17.1 MB, matching the sizes reported in the paper. The other 243 fine-tuned checkpoints are not included; they are reproducible from `config/` and `tools/`. |
| `catalogue_gate/` | The executable-action catalogue frozen with its SHA-256, the gate implementation that withholds out-of-policy output in the service path, its unit and service-path tests, the test log, and the gate measurement replayed over 30,000 stored predictions (Table 3 of the paper). |
| `audits/` | The provenance audit of all 30 hold-out evaluations, the post hoc corpus-overlap screen of the two post-selection sets, the paired frame-cluster bootstrap for the headline model difference, and the blinded author audit and frame audit sheets. |
| `analysis/` | Per-series analysis outputs behind the reported numbers: width, K_eff, depth, common-subset, ring and common-K48 analyses, seed-level statistics, quantization equivalence, final-model and error-decomposition tables, deployment-benchmark summaries and the run inventory. |
| `tables/` | Source tables T01–T12 and the supplementary series as CSV + Markdown, with `README.md` listing captions and sources. |
| `plots/` | Analysis figures as PNG and PDF with the plotted numbers in `data/*.csv`. These carry the numbering of the analysis pipeline, not of the submitted manuscript; for the paper's own figures see `manuscript/figures/`. |
| `tools/` | The training and evaluation runner and launchers, data and tokenizer builders, the policy uniqueness check, and every analysis script whose output appears in `analysis/`, `catalogue_gate/` or `audits/`. |
| `MANIFEST.sha256` | SHA-256 of every file in this record. |

## Reproducing the paper's numbers

1. Unpack `evaluation_outputs/*.tar.gz` under `backend/reports/` and `datasets/keff_series.tar.gz` under
   `backend/models/compact_llm/datasets/`; the scripts expect the repository layout described in `tools/`.
2. Run the analysis scripts in `tools/` (for example `analyze_width_series.py`, `analyze_keff_series.py`,
   `analyze_depth_l3.py`, `keff_common_subset.py`, `seed_level_stats.py`, `quant_equivalence.py`). Their outputs
   should match `analysis/` bit for bit.
3. `tools/measure_policy_gate.py` reproduces Table 3 by replaying the deployed gate over the stored predictions;
   `tools/paired_cluster_holdout.py` reproduces the frame- and family-resampled intervals for the headline model
   difference.
4. `tables/make_tables.py` and the plotting scripts regenerate `tables/` and `plots/`.

## Re-running the training series

`tools/run_*_series.sh` call `run_scale_grid.py` with the frozen configurations (`--scale-config
config/<series>.json`). Hardware used: two NVIDIA GeForce RTX 5090 (32 GB) for training and GPU evaluation; the
CPU deployment benchmark ran on an Intel Core Ultra 9 285K restricted to four threads.

## Scope and what is not included

- **No human-subject data.** The manuscript reports no research involving human participants or human-derived
  data, and this record contains none. The generator scripts under `tools/` and `plots/` retain code paths for a
  human-evaluation figure and table from an earlier draft; those outputs and their inputs are not included.
- The stress set was generated and back-labelled through the Gemini API (model `gemini-3.1-flash-lite`, called
  13 September 2026, temperature 1.0 for generation and 0.0 for back-labelling, 432 calls). Prompts, all
  candidates, the accept/reject decisions with reasons and the raw responses are released so the set can be
  audited, rebuilt or replaced with another generator. **No API credentials appear in any released file.**
- Checkpoints other than the selected model, and the 112 pretraining runs, are not included; their counts and
  configurations are in `analysis/run_inventory_counts.json` and `config/`.

## Licence and third-party notice

Code and data in this record are released under the licence in `LICENSE`. The pretraining corpus derives from the
KOTE dataset, published by its authors under the MIT licence, which permits redistribution provided the copyright
and permission notice accompanies it; that notice is reproduced in `NOTICE_KOTE.txt`. The decontamination record,
token counts and hashes are included with the corpus.
