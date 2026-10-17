A network needs more than sums, products and exponentials. Add the rest of arithmetic to `Value`: `-a`, `a - b` and `a / b`, with a number on either side, and `a ** p` for a number `p`. Then write `log`, `tanh` and `relu` as functions of a Value, as `exp` is. Each needs its derivative:

| Operation | Its derivative |
| --- | --- |
| `$a^p$` | `$p \, a^{p-1}$` |
| `$\log a$` | `$1/a$` |
| `$\tanh a$` | `$1 - \tanh^2 a$` |
| `$\max(a, 0)$` | 1 where `$a > 0$`, and 0 elsewhere, at 0 too, as PyTorch has it |

Subtraction and division can be made from what's there, `$a - b = a + (-1)\,b$` and `$a / b = a \, b^{-1}$`, and then their gradients come from the steps they're made of.

```
-a, a - b, a / b, a ** p, with a number on either side of - and /
log(a), tanh(a), relu(a)
```

The tests compare your values and gradients with PyTorch's on {% $fig.cases %} random expressions saved in `references/scalars.json`, each of {% $fig.steps %} steps on {% $fig.inputs %} numbers that use every operation.
