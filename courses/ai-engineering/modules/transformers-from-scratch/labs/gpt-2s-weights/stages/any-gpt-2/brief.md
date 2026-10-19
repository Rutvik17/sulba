The app's team wants to offer GPT-2's larger sizes too, and any model saved the way GPT-2 is. Your `gpt2` builds GPT-2 small whatever its file holds, and it trusts the file. A download cut short, or a file that isn't a GPT-2's, should stop the app with an error, not give it a model that predicts with the wrong numbers.

OpenAI published GPT-2 in four sizes:

| Size | Width | Blocks | Heads |
| --- | --- | --- | --- |
| Small | {% $fig.small_width %} | {% $fig.small_layers %} | {% $fig.small_heads %} |
| Medium | {% $fig.medium_width %} | {% $fig.medium_layers %} | {% $fig.medium_heads %} |
| Large | {% $fig.large_width %} | {% $fig.large_layers %} | {% $fig.large_heads %} |
| XL | {% $fig.xl_width %} | {% $fig.xl_layers %} | {% $fig.xl_heads %} |

A file's tensors give a GPT's vocabulary, context, width and blocks, by their shapes and names, but not its heads, which split each block's width without a parameter of their own. Every size's heads are {% $fig.head %} wide, so the heads are the width over {% $fig.head %}.

In `load.py`, write:

- `configuration(header)`, the `(vocab, context, width, layers, heads)` of the GPT-2 whose header this is, as your `header` gives it. Raise `ValueError` when the header isn't a GPT-2's: a tensor is missing, a tensor isn't one GPT-2 has, a tensor's shape isn't the one the configuration gives it, or the width isn't a whole number of heads. The causal masks, `h.N.attn.bias`, may be there or not.
- `load(path)`, the GPT-2 in the safetensors file at `path`: your GPT of its configuration, with every parameter copied from the file, in evaluation mode. Raise `ValueError` when the file is damaged or its header isn't a GPT-2's.

A file is damaged when it's shorter than its header says, its header isn't a JSON object, a tensor isn't `F32` or its bytes don't fit its shape, or its tensors' bytes overlap, leave a gap or don't end where the file does. The format requires the tensors to cover every byte after the header, once.

```
configuration(header) -> (vocab, context, width, layers, heads)
load(path) -> GPT
```

Two tests run on every attempt. Then four checks run before the code ships.
