Splitting a vector of `width` numbers into heads costs nothing: the heads are slices of the same layers' outputs, so `MultiHeadAttention(width, heads)` holds `$4 \cdot \text{width}^2 + 4 \cdot \text{width}$` parameters however many heads it has. GPT-2's layer, {% $fig.width %} wide in {% $fig.heads %} heads of {% $fig.size %}, holds {% $fig.params %}.

The view and the transpose are what make the slices heads. A view of `(batch, length, width)` as `(batch, heads, length, width / heads)` without the transpose would also run, and give the right shape, but it would fill each head with a run of numbers from several tokens. Attention would then mix the parts of different tokens as if they were positions.

A layer's work has two parts. Its four layers each multiply every token by a `width` by `width` matrix, `$4 \cdot L \cdot \text{width}^2$` multiply-adds for `$L$` tokens. The scores and the mix of the values take `$L \cdot L \cdot \text{width}$` each, `$2 \cdot L^2 \cdot \text{width}$` in all, which grows with the square of the story's length. PyTorch's counter gives, for GPT-2's layer on its {% $fig.context %} tokens:

| Part | Multiply-adds |
| --- | --- |
| The four layers | {% $fig.projections %} |
| Scores and values | {% $fig.mixing %} |

The two parts are equal at `$L = 2 \cdot \text{width}$`, {% $fig.even %} tokens for GPT-2's width, and past that the scores cost more than the layers.

`nn.MultiheadAttention` keeps the query, key and value layers in one matrix, `in_proj_weight`, which makes all three with one matrix multiply. GPT-2 holds them the same way. Its mask is `True` where a query may not see a key, the opposite of `F.scaled_dot_product_attention`'s, so a mask passed from one to the other must be inverted.
