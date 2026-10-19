A GPT puts the blocks together. It looks up each token's vector in a table of token embeddings, adds the vector of its position from a table of position embeddings, runs the blocks in order, and normalizes the result once more. Its logit for each token of its vocabulary is the dot product of that vector with the token's own embedding: the output layer is the token embedding table itself, tied, so the model reads and writes tokens with the same vectors.

Each block adds two outputs to the residual stream, so a model of `$L$` blocks adds `$2L$` of them. GPT-2's paper scales the starting weights of the layers that write to the stream by `$1/\sqrt{N}$`, `$N$` the number of those additions, so the stream keeps the same size however deep the model is. Hugging Face's GPT-2 starts each layer that writes to the stream from a normal distribution with a standard deviation of {% $fig.std %} over `$\sqrt{2L}$`, all its other weights, the embeddings' included, with {% $fig.std %}, its biases at 0, and its layer normalizations' weights at 1.

In `block.py`, write `GPT(vocab, context, width, layers, heads)`, an `nn.Module` with GPT-2's names for its parts:

- `wte`, an `nn.Embedding(vocab, width)`, and `wpe`, an `nn.Embedding(context, width)`;
- `blocks`, an `nn.ModuleList` of `layers` blocks, and `ln_f`, a final `LayerNorm(width)`;
- no other parameters: its output layer is `wte`'s weight.

Its weights start as Hugging Face's GPT-2's do: the layers that write to the stream are `attn.out` and `mlp.proj`. `forward(tokens)` takes token numbers `(batch, length)` and gives the logits `(batch, length, vocab)`. It raises `ValueError` for a story longer than `context`.

```
GPT(vocab, context, width, layers, heads)
forward(tokens) -> logits (batch, length, vocab)
```

The tests build GPT-2's four sizes on PyTorch's meta device, which makes tensors without memory, and count their parameters.
