The survey will classify its tiles with what it learns from {% $fig.labelled %} labelled tiles of each kind. Stage 3's probe, on the class token of tiles at {% $fig.side %} pixels, gives {% $fig.baseline %} of the survey's {% $fig.tested %} test tiles their kinds, at {% $fig.baseline_macs %} multiply-adds a tile. The survey wants at least {% $fig.target %}, within its budget of {% $fig.budget %} multiply-adds a tile. In `survey.py`, write:

- `train(tiles, kinds)`, a classifier learned from labelled tiles from `read` and their kinds' numbers.
- `classify(classifier, tiles)`, the kind's number it gives each tile, as an `int64` tensor.

The classifier is yours to design: what it takes from the backbone, at what size it gives the backbone tiles, and what it learns from them. Your `tiles.py`, `backbone.py` and `probe.py` are there to build on, and `DinoViT`'s `tokens(images)` gives every token after the last norm, the class token first and then each patch's.

```
train(tiles, kinds) -> classifier
classify(classifier, tiles) -> int64 tensor (N,)
```
