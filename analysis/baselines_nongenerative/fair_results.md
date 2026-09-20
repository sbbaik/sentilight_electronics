# Non-generative baselines, fair comparison and diagnostics

Training rows 49093; classes present in training 240/240; rows per class min 18, median 234, max 340.

| model | train | val | dev test | unseen-frame hold-out | paraphrase hold-out | CPU median ms | note |
|---|--:|--:|--:|--:|--:|--:|---|
| sbert_frozen_logreg | 98.2 | 95.4 | 30.8 | 17.4 | 9.8 | nan |  |
| sbert_deployed_finetuned_logreg | 25.0 | 22.0 | 5.0 | 3.0 | 0.9 | 6.0 | encoder fine-tuned for the deployed similarity objective, head trained here |
| sbert_deployed_adapter_prototype | nan | nan | 2.3 | 1.8 | — | 6.0 | the deployed SBERT condition: fine-tuned encoder, nearest prototype example, profile's lighting tuple |
| encoder_finetuned_240class | 98.6 | 98.3 | 87.7 | 69.6 | 22.2 | 5.1 |  |

Diagnostics:
```
{
 "dataset": {
  "train_rows": 49093,
  "classes_in_train": 240,
  "reachable_tuples": 240,
  "classes_missing_from_train": 0,
  "rows_per_class_min": 18,
  "rows_per_class_median": 234,
  "rows_per_class_max": 340,
  "imbalance_max_over_min": 18.89,
  "dev_classes_unseen_in_train": 0,
  "holdout_classes_unseen_in_train": 0,
  "label_alignment_check": "classes sorted once; cid maps tuple->index; predictions decoded via classes[i]"
 },
 "frozen_sbert": {
  "embedding_dim": 384,
  "norm_mean": 1.0,
  "distinct_train_embeddings": 24063,
  "note": "vectors are L2-normalised (norm 1.0); distinct-embedding count shows how many training utterances the frozen encoder separates at all"
 }
}
```
