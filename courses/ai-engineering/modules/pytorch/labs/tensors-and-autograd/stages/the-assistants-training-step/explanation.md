The assistant's tests each looked where the problems weren't. A loss that falls over a few steps on one batch says nothing of the hidden layer, since the output layer alone can lower it, and steps that grow as their gradients add up still lower it at first. A mean of 0 holds whatever spread the pixels are divided by. And no test asked what training does to the arrays it's given.

---

Each problem is one of PyTorch's ways that NumPy doesn't share: gradients that add up until something clears them, a graph that ends wherever `.detach()` cuts it, a spread with Bessel's correction, and tensors that share the memory of the arrays they're made from. A port is checked against the code it replaces, number for number, every layer and every step, and against what it does to what it's given.
