Each of the assistant's tests checked something a wrong optimizer gets right too: momentum at a learning rate that never changed, the direction and the scale of Adam's step, a decay that shrank the weights, and a step read back from the optimizer's own list. None of them compared a step with PyTorch's.

---

The checks used the optimizers as training does: through a schedule, from the first step on, with the decay doing all the work, and on a network that holds its own arrays. Recorded steps are the strongest test of an optimizer, as in stages 1 to 3, since every number of every step has to agree, not only its direction or its size.
