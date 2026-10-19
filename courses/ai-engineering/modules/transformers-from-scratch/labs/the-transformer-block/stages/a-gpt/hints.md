`self.wte(tokens) + self.wpe(torch.arange(length, device=tokens.device))` broadcasts the positions' vectors over the batch.

---

`self.ln_f(x) @ self.wte.weight.T` is the tied output layer: one logit for every token of the vocabulary.

---

`self.named_parameters()` gives each parameter with its name, such as `blocks.0.mlp.proj.weight`, so `name.endswith(...)` finds the layers that write to the stream. `torch.nn.init.normal_(param, std=...)` sets a parameter in place.
