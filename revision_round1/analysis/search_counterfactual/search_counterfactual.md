# Counterfactual: a width search confined to the enumeration-informed region

Region: d ∈ [256, 384] (§3.3).

## 24k production tokenizer (W series, L = 8)

- full grid: widths [128, 192, 224, 256, 320, 384, 512], 33 fine-tuning runs
- confined grid: widths [256, 320, 384], 13 runs (20 fewer)
- best point estimate, full grid: d = 320 (81.9 %, 3 seeds)
- best point estimate, five-seed cells: d = 512 (81.6 %)
- best point estimate inside region: d = 320 (81.9 %)
- selected: d = 384 (inside region: True)

- step 384→512: +0.8 pp; the paper's adoption rule (Holm-corrected row-level p < 0.05 and all seeds agreeing in sign) was not met for this step; width above 384 was not adopted

## 4k natural tokenizer (X series, L = 8)

- full grid: widths [224, 256, 320, 384], 20 fine-tuning runs
- confined grid: widths [256, 320, 384], 15 runs (5 fewer)
- best point estimate, full grid: d = 384 (86.5 %, 5 seeds)
- best point estimate, five-seed cells: d = 384 (86.5 %)
- best point estimate inside region: d = 384 (86.5 %)
- selected: d = 384 (inside region: True)

## Reading

Under the 24k tokenizer the full grid (7 widths, 33 runs) and the region-confined grid (3 widths, 13 runs) lead to the same adopted width: the only reliable gain lies between d = 224 and 256, inside the region, and the step to 512 was not adopted under the prospective rule. Under the 4k tokenizer the selected d = 384 is the argmax of both the full grid (4 widths, 20 runs) and the confined grid (3 widths, 15 runs). In both series the enumeration-informed region contained the width that was eventually chosen, and confining the search to it would have cost 20 fewer runs in one series and 5 in the other. This is a reading of a grid whose outcome was already known: it shows the region was not misleading, not that a practitioner could have known in advance to trust it, and the wider sweep is what established that the region was right under one tokenizer and too low under the other.
