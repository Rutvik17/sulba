Loop over the parameters and their gradients together, `for number, (param, grad) in enumerate(zip(self.params, grads))`, and keep each parameter's buffer in `self.buffers[number]`.

---

Add the weight decay into a new array, `grad = grad + self.weight_decay * param`. The gradient belongs to the layer that made it, so never change it in place.

---

At the first step the buffer is a copy of the gradient, `np.copy(grad)`, with no dampening. After it, the buffer is `self.momentum * buffer + (1 - self.dampening) * grad`.

---

With Nesterov's momentum the step's gradient is `grad + self.momentum * buffer`, and without it the buffer itself. Then `param -= self.lr * grad` changes the array in place.
