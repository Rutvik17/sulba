The clinic's data team is trying a small neural network on the {% $fig.measurements %} measurements. Each standardized sample goes through a hidden layer of {% $fig.hidden %} tanh units, and a weighted sum of their outputs gives a score `$s$`, whose sigmoid is the probability that the sample is malignant:

```math
A = \tanh(Z W_1 + b_1), \qquad s = A w_2 + b_2
```

Write `network_loss`, the mean log loss of those probabilities, `$\frac{1}{n} \sum_k \left(\log(1 + e^{s_k}) - y_k s_k\right)$`. `np.logaddexp(0, s)` works out `$\log(1 + e^s)$` and stays finite for a score of any size, where `np.exp` overflows.

Training the network needs the loss's gradient with respect to all {% $fig.parameters %} weights and biases. Write `network_gradient` by the chain rule: start at the loss and work back through each step, reusing the hidden layer's outputs. Two derivatives do most of the work: the loss's derivative with respect to a sample's score is `$(\sigma(s_k) - y_k)/n$`, and tanh's derivative is `$1 - \tanh^2$`.

```
network_loss(params, Z, y) -> a number
network_gradient(params, Z, y) -> (dW1, db1, dw2, db2)
```

The tests compare your gradient with central differences at random weights and at zero, for the clinic's {% $fig.records %} records and for a single sample.
