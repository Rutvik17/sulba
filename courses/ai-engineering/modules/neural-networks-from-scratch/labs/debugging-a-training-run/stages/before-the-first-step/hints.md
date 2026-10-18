The network's number of classes is the length of its last bias, `len(params[-1])`.

---

Copy the arrays first, `params = [param.copy() for param in params]`, then record each step's loss before `param -= lr * grad` for each parameter and its gradient.
