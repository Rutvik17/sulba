The survey wants to try fine-tuning: training the backbone itself on the labelled tiles, not only a layer on top of it. It asked an assistant, who wrote `finetune.py`, and its five tests all pass.

Review it as if the survey were about to fine-tune with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the survey will use it. A run shows how many pass. You see which ones when you finish the review.

The survey's request:

- `Classifier(backbone, count)`: the backbone, with `head`, a linear layer that gives each of `count` kinds a score from the backbone's features.
- `kind_names(archive)`: each kind's name, at the number `tiles.py` gives it.
- `scores(model, tiles, side)`: the classifier's scores for tiles from `read`, prepared by `prepare`, without tracking gradients.
- `warm_up(model, tiles, kinds, side, epochs, size, generator)`: trains the head alone with AdamW, for `epochs` epochs in random batches of `size` tiles, each flipped left to right at random and prepared as `scores` prepares tiles. The backbone stays frozen and works out no gradients.
- `fine_tune(model, tiles, kinds, side, epochs, size, generator)`: trains every layer the same way, the head at `HEAD_RATE` and the backbone at the smaller `BACKBONE_RATE`.
- `survey_classifier(tiles, kinds, side, warmup, epochs, size, seed)`: a classifier warmed up and then fine-tuned on the labelled tiles, with every chance in its training decided by `seed`.
