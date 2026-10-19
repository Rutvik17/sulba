`torch.tensor` of a list of ints gives `torch.long`, the type an embedding reads.

---

`starts[:, None] + torch.arange(length + 1)` gives the place of every token of each window, with its last target. Index the stream with it, then take the inputs as all but the last token, and the targets as all but the first.

---

A generator function loops with `while True:` and gives each batch with `yield`. Draw a new `torch.randperm(count, generator=generator)` at the start of each pass.

---

`F.cross_entropy(logits.flatten(0, 1), targets.flatten(), reduction="sum")` adds up a batch's losses, so you can divide by the number of targets once at the end. `model.training` says which mode the model is in, and `model.train(mode)` puts it back.
