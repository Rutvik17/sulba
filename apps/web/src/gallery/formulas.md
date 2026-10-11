The sigmoid `$\sigma(z)$` turns any score `$z \in \mathbb{R}$` into a probability `$p \in (0, 1)$`:

```math
\sigma(z) = \frac{1}{1 + e^{-z}}
```

The loss averages the cost of each prediction, plus a penalty on large weights:

```math
\begin{aligned}
L(w, b) &= -\frac{1}{n} \sum_{i=1}^{n} \bigl[\, y_i \ln p_i + (1 - y_i) \ln(1 - p_i) \,\bigr] \\
&\quad + \frac{\lambda}{2} \lVert w \rVert^2
\end{aligned}
```

Gradient descent steps each weight against its derivative, at a learning rate `$\eta > 0$`:

```math
\frac{\partial L}{\partial w} = \frac{1}{n} X^\top (p - y) + \lambda w,
\qquad
w \leftarrow w - \eta \, \frac{\partial L}{\partial w}
```

Attention weighs each value by how well its key matches the query:

```math
\operatorname{Attention}(Q, K, V) = \operatorname{softmax}\!\left( \frac{Q K^\top}{\sqrt{d_k}} \right) V
```
