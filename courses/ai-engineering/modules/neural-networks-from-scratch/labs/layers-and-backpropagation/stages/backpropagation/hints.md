`forward` is a loop, `for layer in self.layers: X = layer.forward(X)`, and returns what comes out of the last layer.

---

`backward` is the same loop over `reversed(self.layers)`, passing the gradient along: `d = layer.backward(d)`.

---

`step` needs only the layers with weights, `isinstance(layer, Linear)`. `layer.weight = layer.weight - lr * layer.dweight` makes a new array, and leaves the one the layer was given as it was.

---

`bound = 1 / np.sqrt(inputs)`, then `rng.uniform(-bound, bound, size=(outputs, inputs))` for the weight and `rng.uniform(-bound, bound, size=outputs)` for the bias.
