Give `Adam.__init__` a `decoupled_weight_decay=False` argument and keep it on `self`, as the other settings are.

---

In `Adam.step`, decay the weight in place before anything else when the flag is on, `param *= 1 - self.lr * self.weight_decay`, and add the decay to the gradient only when it's off.

---

`AdamW.__init__` is one call: `super().__init__(params, lr, betas, eps, weight_decay, decoupled_weight_decay=True)`.
