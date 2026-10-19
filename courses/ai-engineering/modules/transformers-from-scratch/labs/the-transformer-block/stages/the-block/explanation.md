The residual stream helps a deep model train. Each part adds to the stream rather than replacing it, so the gradient of the loss reaches every block directly, through the additions, as well as through the parts, and a block whose parts add nothing passes its input on unchanged.

The layer normalizations sit at each part's input, inside its branch, so the stream itself is never normalized: GPT-2 moved them there from the outputs of the original transformer, and added one more after the last block. A part reads the stream at a steady size, however large it grows.

GELU is smooth where ReLU has a corner: it weighs `$x$` by how likely a standard normal variable is to fall below it, `$x \, \Phi(x)$`, so it lets a little of a negative input through. Its tanh form is an approximation, which GPT-2 trained with, so its weights expect it. From {% $fig.low %} to {% $fig.high %}, the two forms differ by at most {% $fig.gap %}.

The MLP holds most of a block's parameters: `$8 n^2 + 5n$` of the `$12 n^2 + 13n$`, at a width of `$n$`. At GPT-2's {% $fig.width %}, that is {% $fig.mlp %} of {% $fig.block %}, {% $fig.share %}.
