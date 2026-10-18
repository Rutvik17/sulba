Record the smoothed loss before checking it against `stop` and before the step, so that the step it stops at is the last one returned.

---

`zip(lrs, batches, strict=True)` pairs each learning rate with its batch, and `enumerate(..., start=1)` counts the steps from 1 for `$1 - \beta^t$`.
