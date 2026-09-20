# Size-matched discriminative control: CompactLM backbone with a 240-class head

Same pretrained checkpoints as the generative models (seeds [42, 43, 44, 45, 46]), same 240 classes, 4 epochs, lr 0.0003.

- parameters 15,790,704 (generative model 15,698,304)
- development test exact 87.2 ± 0.7 %
- unseen-frame hold-out exact 58.3 ± 2.3 %
- paraphrase hold-out exact 10.3 ± 0.6 %
- per seed hold-out: 55.1, 59.2, 56.6, 59.9, 60.6
- CPU median latency 3.5 ms (4 threads)
