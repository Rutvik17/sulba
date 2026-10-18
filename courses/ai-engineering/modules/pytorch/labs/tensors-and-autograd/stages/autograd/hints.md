`torch.tensor(array, requires_grad=True)` copies an array into a tensor that autograd follows. `torch.from_numpy` would share the array's memory, and a step made in place would change it.

---

`F.cross_entropy(logits, digits)` is the mean cross-entropy, as the NumPy reader's. `torch.autograd.grad(loss, inputs)` gives the loss's gradient with respect to each input, without touching `.grad`.

---

`loss.backward()` adds each gradient to its parameter's `.grad`. Change the parameters inside `with torch.no_grad():`, so autograd doesn't record the step, and clear `.grad` afterwards, or the next step adds to it.
