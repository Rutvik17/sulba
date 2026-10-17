Made from `+`, `*` and `**`, subtraction and division need no backward passes of their own: the engine records the steps they're made of, and the chain rule through those steps gives `$\partial (a/b) / \partial b = a \cdot (-b^{-2})$` without anyone writing it. The cost is more steps for the same result, `$a / b$` as a power and a product, which a backward pass then walks one at a time. PyTorch gives each of its operations its own derivative, so that one step does.

`tanh` and `exp` have derivatives that come from their own outputs, `$1 - \tanh^2 a$` and `$e^a$`, so their backward passes reuse what the forward pass worked out. `log`'s needs its input, and is defined only where the input is above 0, which is why the tests' random expressions take logs only of numbers above 0.

The chart takes the slope of `$a^p$` from your engine at each point and draws it over `$p \, a^{p-1}$`: each slope is a backward pass from a single power.
