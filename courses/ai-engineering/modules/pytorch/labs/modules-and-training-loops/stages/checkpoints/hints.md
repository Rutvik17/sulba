An optimizer has a `state_dict()` too. SGD with momentum keeps a momentum buffer for each parameter, and a new optimizer starts without them.

---

`batches.generator.get_state()` gives the generator's state as a tensor of bytes, and `set_state` puts it back, so the next epoch deals the order the stopped run would have.

---

`torch.save` writes a dict of state dicts, tensors and numbers, and `torch.load` reads it back. By default, `torch.load` builds only tensors, plain types such as numbers and lists, and dicts.
