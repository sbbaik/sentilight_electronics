#!/usr/bin/env bash
# Rebuild the inputs of revision_round1/ from the archives of the v1.0.0 record (run from anywhere).
# After this, every script in revision_round1/tools/ runs with the package as its only input.
set -euo pipefail
R="$(cd "$(dirname "$0")" && pwd)"; PKG="$(cd "$R/.." && pwd)"
x() { tar xzf "$1" -C "$2" "${@:3}"; }
mkdir -p "$R/data/per_row" "$R/data/datasets" "$R/data/tables" "$R/models/tokenizers" "$R/models/doi_release" "$R/_tmp"
# per-row evaluation outputs
x "$PKG/evaluation_outputs/scale_grid_vocab_natural.tar.gz" "$R/_tmp" scale_grid_vocab_natural/V4k/per_row
x "$PKG/evaluation_outputs/holdout_final.tar.gz"             "$R/_tmp" holdout_final/per_row
x "$PKG/evaluation_outputs/holdout_paraphrase.tar.gz"        "$R/_tmp" holdout_paraphrase/per_row
x "$PKG/evaluation_outputs/baselines_nongenerative.tar.gz"   "$R/_tmp" baselines_nongenerative/classifier_instrumented/per_row
rm -rf "$R/data/per_row/dev_V4k" "$R/data/per_row/unseen_frames" "$R/data/per_row/stress" "$R/data/per_row/head"
mv "$R/_tmp/scale_grid_vocab_natural/V4k/per_row" "$R/data/per_row/dev_V4k"
mv "$R/_tmp/holdout_final/per_row"               "$R/data/per_row/unseen_frames"
mv "$R/_tmp/holdout_paraphrase/per_row"          "$R/data/per_row/stress"
mv "$R/_tmp/baselines_nongenerative/classifier_instrumented/per_row" "$R/data/per_row/head"
# datasets
x "$PKG/datasets/keff_series.tar.gz"          "$R/_tmp" keff_series/K240
x "$PKG/datasets/holdout_unseen_frames.tar.gz" "$R/_tmp" holdout_unseen_frames/K240
x "$PKG/datasets/holdout_paraphrase.tar.gz"    "$R/_tmp" holdout_paraphrase/K240
rm -rf "$R/data/datasets/K240_keff" "$R/data/datasets/holdout_natural_K240" "$R/data/datasets/holdout_paraphrase_K240"
mv "$R/_tmp/keff_series/K240"           "$R/data/datasets/K240_keff"
mv "$R/_tmp/holdout_unseen_frames/K240" "$R/data/datasets/holdout_natural_K240"
mv "$R/_tmp/holdout_paraphrase/K240"    "$R/data/datasets/holdout_paraphrase_K240"
# tables (CSV only) and tokenizers
cp "$PKG"/tables/*.csv "$R/data/tables/"
for t in natural_corpus_V2 production_24k template_corpus_V1; do rm -rf "$R/models/tokenizers/$t"; x "$PKG/tokenizers/$t.tar.gz" "$R/models/tokenizers"; done
# the selected model: the package's own files
rm -rf "$R/models/doi_release/selected_d384_L8_V4k"; ln -s "$PKG/models/selected_d384_L8_V4k" "$R/models/doi_release/selected_d384_L8_V4k"
rm -rf "$R/_tmp"
echo "inputs ready under $R (per_row: $(ls "$R"/data/per_row/*/ | grep -c jsonl) files)"
