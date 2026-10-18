A map-style dataset needs `__len__` and `__getitem__`. A `DataLoader` over it gathers a batch of items and stacks them, so each batch is a tensor of pixels and a tensor of digits.

---

`DataLoader(digits, batch_size=64, shuffle=True, generator=generator)` deals the digits in a new order each epoch, drawn from `generator`, here `torch.Generator().manual_seed(seed)`.

---

`reader.training` says which mode the reader is in, and `reader.train(mode)` puts it back. Sum each batch's loss with `reduction="sum"`, so every digit counts the same in the mean.
