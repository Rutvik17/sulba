With the file read and text in GPT-2's tokens, GPT-2's weights can go into the app's own GPT, the one you built in The transformer block lab, which `gpt2.py` holds. GPT-2's file names each tensor for OpenAI's code, and your GPT names its parameters its own way:

| In GPT-2's file | In your GPT |
| --- | --- |
| `wte.weight`, `wpe.weight`, `ln_f.weight`, `ln_f.bias` | The same |
| `h.0.ln_1.weight`, `h.0.ln_2.bias`, and so on | `blocks.0.ln_1.weight`, `blocks.0.ln_2.bias` |
| `h.0.attn.c_attn.weight` | `blocks.0.attn.qkv.weight` |
| `h.0.attn.c_proj.weight` | `blocks.0.attn.out.weight` |
| `h.0.mlp.c_fc.weight` | `blocks.0.mlp.fc.weight` |
| `h.0.mlp.c_proj.weight` | `blocks.0.mlp.proj.weight` |

The same goes for every block, and for the linear layers' biases. Two more differences:

- GPT-2's code multiplies `x @ weight`, so it keeps each linear layer's weight as (inputs, outputs), where `nn.Linear` keeps (outputs, inputs). Copy each of those weights turned around, with `.T`.
- Each block's `attn.bias` is a causal mask, not a parameter. Leave it out.

Your GPT's output layer is the token embeddings' own weight, so it comes with `wte.weight`.

In `gpt2.py`, write:

- `load(model, weights)`, the model, with each tensor in `weights`, by its name in GPT-2's file, copied into its parameter. It must set every parameter, and raise `ValueError` when a tensor has no parameter to go to, or a parameter has no tensor to come from.
- `gpt2(path)`, GPT-2 small: a GPT with a vocabulary of {% $fig.vocab %} and a context of {% $fig.context %}, {% $fig.width %} wide, with {% $fig.blocks %} blocks of {% $fig.heads %} heads, given the weights in the file at `path` as your `tensors` reads them, in evaluation mode.

```
load(model, weights) -> model
gpt2(path) -> GPT
```

The tests compare your GPT-2's logits, in float64, with those Hugging Face's transformers library gives for the same tokens, and load GPTs of other sizes from tensors of their own.
