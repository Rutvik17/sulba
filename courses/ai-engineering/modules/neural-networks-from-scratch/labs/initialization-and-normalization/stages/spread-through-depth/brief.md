The office tried a deeper network: {% $fig.hidden %} hidden layers of {% $fig.width %} ReLUs, each started as `torch.nn.Linear` starts. After {% $fig.steps %} steps of SGD at a learning rate of {% $fig.lr %} it read {% $fig.read %} of the validation digits, and its loss was {% $fig.loss %}: ln 10, {% $fig.guess %}, the loss of a guess among ten digits. It never learned. Its signal faded on the way through: each layer started that way keeps about {% $fig.default %} of the size of its input, so after {% $fig.hidden %} layers almost nothing is left to learn from, and the gradients on the way back fade the same way.

A layer keeps the size of the signal when its starting range suits its inputs and the nonlinearity after it. `torch.nn.init` draws each weight from `$U(-a, a)$`, with:

```math
a_{\text{Xavier}} = g \sqrt{\frac{6}{n_{\text{in}} + n_{\text{out}}}}, \qquad a_{\text{Kaiming}} = g \sqrt{\frac{3}{n}}
```

where `$n_{\text{in}}$` and `$n_{\text{out}}$` are the layer's inputs and outputs, `$n$` is one of them, the inputs unless `mode="fan_out"`, and `$g$` is the gain for the nonlinearity: 1 for none or a sigmoid, 5/3 for tanh, `$\sqrt{2}$` for ReLU, `$\sqrt{2 / (1 + s^2)}$` for a leaky ReLU of slope `$s$`, 0.01 unless it's given, and 3/4 for SELU.

Write `calculate_gain`, `xavier_uniform` and `kaiming_uniform`, as `torch.nn.init` has them. A weight's shape is `(outputs, inputs)`, as `nn.Linear` keeps it, and `fans` gives you both.

```
calculate_gain(nonlinearity, param=None), raising ValueError for a nonlinearity it doesn't know
xavier_uniform(shape, rng, gain=1.0) -> a weight of shape
kaiming_uniform(shape, rng, a=0.0, mode="fan_in", nonlinearity="leaky_relu") -> a weight of shape
```

`kaiming_uniform`'s `a` is the slope its gain takes. The tests compare your ranges with the largest weights PyTorch drew for each setting, recorded in `references/init.json`.
