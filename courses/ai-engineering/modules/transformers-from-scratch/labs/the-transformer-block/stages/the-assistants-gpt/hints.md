Compare each block's `forward` with the two additions you wrote in stage 2.

---

`self.head.weight.data.copy_(...)` copies numbers. Assigning the parameter itself, `self.head.weight = self.wte.weight`, shares it.

---

Count the layers that write to the residual stream, and check how their weights start.
