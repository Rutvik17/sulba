`torch.optim.AdamW` takes a list of parameter groups, each a dict with its `"params"` and its own `"weight_decay"`. `param.dim() >= 2` picks the matrices.

---

Set the learning rate for each step on every group: `for group in optimizer.param_groups: group["lr"] = ...`.

---

`torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)` goes after `loss.backward()` and before `optimizer.step()`.

---

`model(torch.tensor([tokens[-model.context:]]))[0, -1]` gives the logits for the token after the last one. Write under `torch.no_grad()`, since nothing learns from it.
