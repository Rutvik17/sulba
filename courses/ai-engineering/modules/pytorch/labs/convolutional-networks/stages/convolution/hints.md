`F.pad(x, (left, right, top, bottom))` adds zeros around the photo. Then kernel position `(i, j)` sees a strided slice of it: rows from `i * dilation` on, `stride` apart, as many as the output has, and columns likewise from `j * dilation`.

---

Stack the slices of every kernel position into one tensor of shape `(N, C, kh, kw, H_out, W_out)`. The convolution is then one `torch.einsum`, which multiplies and sums over the channels and the kernel positions together.

---

For groups, reshape the channels of that tensor to `(groups, C / groups)` and the filters to `(groups, O / groups, C / groups, kh, kw)`, so the sum runs within each group, then put the groups' outputs back side by side.

---

For pooling, take the same slices without padding, put each window's pixels last in reading order, and take `.max(dim=-1)`. Along a dimension, `max` sends the gradient to the first largest value, where `amax` splits it among values that tie.
