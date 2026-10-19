Each block of the app's model adds two things to each token's vector: attention's output, then the MLP's. Each part reads the vector through a layer normalization of its own, and adds its output to the vector instead of replacing it, so the vector carries what every part before it added. That running vector is the residual stream:

```math
\begin{aligned}
x &\leftarrow x + \text{attention}(\text{LN}_1(x)) \\
x &\leftarrow x + \text{MLP}(\text{LN}_2(x))
\end{aligned}
```

The MLP works on each token alone: a linear layer to four times the width, GELU, and a linear layer back. GPT-2 uses GELU's tanh form:

```math
\text{GELU}(x) = \frac{x}{2} \left(1 + \tanh\left(\sqrt{2/\pi}\,\left(x + 0.044715\,x^3\right)\right)\right)
```

The starter gives `CausalSelfAttention`, the attention you built in the Attention lab, with its query, key and value layers in one, as GPT-2 holds them. In `block.py`, write:

- `gelu(x)`, GELU's tanh form, without `F.gelu`.
- `MLP(width)`, an `nn.Module` with two `nn.Linear` layers: `fc`, from `width` to `4 * width`, and `proj`, back to `width`. Its `forward(x)` gives `proj(gelu(fc(x)))`.
- `Block(width, heads)`, an `nn.Module` with GPT-2's names for its parts: `ln_1`, a `LayerNorm(width)`; `attn`, a `CausalSelfAttention(width, heads)`; `ln_2`, another `LayerNorm(width)`; and `mlp`, an `MLP(width)`. Its `forward(x)` gives the residual stream after both additions.

```
gelu(x) -> the shape of x
MLP(width)
Block(width, heads)
```

The tests compare `gelu` with `F.gelu(x, approximate="tanh")`, and each block with the same additions made from its own parts.
