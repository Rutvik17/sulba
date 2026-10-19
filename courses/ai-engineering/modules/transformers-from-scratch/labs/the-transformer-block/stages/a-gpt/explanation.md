GPT-2's four sizes differ only in width and depth, with the same vocabulary of {% $fig.vocab %} tokens and context of {% $fig.context %}:

| Size | Width | Blocks | Parameters |
| --- | --- | --- | --- |
| Small | {% $fig.small_width %} | {% $fig.small_layers %} | {% $fig.small_params %} |
| Medium | {% $fig.medium_width %} | {% $fig.medium_layers %} | {% $fig.medium_params %} |
| Large | {% $fig.large_width %} | {% $fig.large_layers %} | {% $fig.large_params %} |
| XL | {% $fig.xl_width %} | {% $fig.xl_layers %} | {% $fig.xl_params %} |

Tying the output layer to the token embeddings saves a matrix of the vocabulary by the width: {% $fig.tied %} parameters in GPT-2 small, {% $fig.tied_share %} of its size. It also means a token's logit rises with how much the final vector points the way of that token's own embedding.

Position embeddings are learnt like token embeddings, one vector for each place in the context, so the model can't read a story longer than its context: it has no vector for position {% $fig.context %}.

Each layer that writes to the residual stream adds its output to it, and at the start those outputs are random, so their variances add up: with `$2L$` of them, the stream's variance would grow in proportion to the depth. Scaling those layers' starting weights by `$1/\sqrt{2L}$` divides each addition's variance by `$2L$`, so their sum stays the same at any depth. In GPT-2 small, with {% $fig.residual %} additions, they start with a standard deviation of {% $fig.deep_std %}.
