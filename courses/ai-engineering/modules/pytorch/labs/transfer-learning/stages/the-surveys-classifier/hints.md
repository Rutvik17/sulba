At {% $fig.side %} pixels a tile takes {% $fig.baseline_macs %} multiply-adds, and at {% $fig.large %}, {% $fig.solution_macs %}. The budget holds several passes at the smaller side, or one at the larger.

---

`tokens[:, 1:].mean(1)` is the mean of the patches' tokens, and `torch.cat((tokens[:, 0], ...), dim=1)` puts it beside the class token. DINOv2's own linear classifiers take both.

---

A tile seen from above has no up. `torch.rot90(tiles, k, (2, 3))` turns tiles by `k` quarter turns and `.flip(3)` mirrors them: the four turns, each mirrored or not, give the square's {% $fig.views %} symmetries.
