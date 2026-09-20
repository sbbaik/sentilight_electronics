# Before publishing this record

Three items need an author decision or action. Everything else in this folder is ready.

- [X] **Licence.** `LICENSE` still reads "proposed … to be confirmed". Decide the arrangement (the proposal is
      CC BY 4.0 for data, tables, figures, evaluation outputs and model weights; MIT for the code under `tools/`),
      replace `LICENSE` with the actual licence text, and set the matching field in `CITATION.cff`, `.zenodo.json`
      and the Zenodo web form.
- [ ] **Publish the record and copy the DOI into the manuscript.** The Data Availability Statement of
      `manuscript/SentiLight_Electronics_v44.docx` still carries `[AUTHORS: supply before submission]` where the
      DOI belongs, and states that the artefacts are not yet public. Both must be updated once the DOI resolves.
- [X] **Confirm the corpus redistribution.** `NOTICE_KOTE.txt` reproduces the KOTE MIT notice as that licence
      requires. Confirm the authors are content to redistribute the decontaminated corpus in
      `datasets/pretrain_corpus_clean_v1.tar.gz`; an earlier internal release had withheld the corpus text.

## Already settled

- ORCID identifiers are recorded in `README.md`, `CITATION.cff` and `.zenodo.json`
  (Baik 0009-0009-4420-4084; Hong 0000-0003-2974-3820).
- Affiliations, corresponding author and the IITP grant number are filled in.

## Verified before packaging

- No human-subject data: the manuscript reports none and the survey ratings of earlier drafts are excluded.
- No API credentials in any released file (scanned across all text-bearing files).
- No reference to a companion paper.
- `MANIFEST.sha256` covers every file.
