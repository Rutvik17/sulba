The assistant's tests use each tensor once, broadcast only a bias, and take each function at one point. Ask what each of those hides.

---

Compare `topological_order`, `unbroadcast` and each operation's `_backward` with yours from stages 1 to 3, line by line.
