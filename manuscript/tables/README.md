# Tables of the manuscript

Exported from the submitted Word file, one CSV per table, in document order.

- `Table01.csv` — Table 1. Executable policies and effective action counts used in the capacity and depth series.
- `Table02.csv` — Table 2. Candidates used for engineering selection, measured on the development test set across five seeds (mean ± sample SD).
- `Table03.csv` — Table 3. Catalogue decisions obtained by replaying the production service's default reject mode on selected-model predictions (five seeds × 2,000 requests per set; mean ± sample SD). These are software decisions, not new bulb operations. Shares withheld and wrong-but-passed use all requests as denominator; the wrong-answer capture column uses only wrong answers. A withheld tuple cannot exactly match policy gold, while an admitted tuple may still be wrong.
- `Table04.csv` — Table 4. Exact tuple match on the development set, newly written frames and post hoc machine-paraphrase set. ± denotes five-seed mean ± sample SD; the fine-tuned MiniLM value is one run.
- `Table05.csv` — Table 5. CPU measurements. Each implementation ran in a separate four-thread process on the same deterministic 300 development prompts after 20 warm-up prompts; fp32 head and fp32 decoder can be compared at matched precision.
