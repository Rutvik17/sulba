With positions in hand, the rest of SmolLM2 can go into a model of your own, which the app can then change: the next stage keeps what it has read. SmolLM2's block differs from the app's GPT's in three more ways:

- **RMSNorm** divides each vector by its root mean square, `$x / \sqrt{\overline{x^2} + \epsilon}$`, then multiplies it by a learnt weight. It subtracts no mean and adds no bias.
- **SwiGLU** is the MLP: `down_proj(silu(gate_proj(x)) * up_proj(x))`. The gate decides how much of each of the up projection's numbers goes through.
- **Grouped-query attention** has {% $fig.heads %} query heads, {% $fig.dim %} wide, but only {% $fig.kv_heads %} key heads and {% $fig.kv_heads %} value heads. Each key and value head serves {% $fig.group %} neighbouring query heads: the first {% $fig.group %} query heads read the first key and value head, the next {% $fig.group %} the second, and so on.

No linear layer has a bias. As in the app's GPT, the output layer is the token embeddings' own weight.

In `smollm.py`, `tensors` reads the file's tensors as float32. Write `rms_norm`, `RMSNorm`, `MLP`, `Attention`, `Block` and `SmolLM`, with the parameters named as in the file without its `model.` prefix:

| In the file | In your model |
| --- | --- |
| `model.embed_tokens.weight` | `embed_tokens.weight` |
| `model.layers.0.input_layernorm.weight` | `layers.0.input_layernorm.weight` |
| `model.layers.0.self_attn.q_proj.weight`, and `k_proj`, `v_proj`, `o_proj` | `layers.0.self_attn.q_proj.weight`, and so on |
| `model.layers.0.post_attention_layernorm.weight` | `layers.0.post_attention_layernorm.weight` |
| `model.layers.0.mlp.gate_proj.weight`, and `up_proj`, `down_proj` | `layers.0.mlp.gate_proj.weight`, and so on |
| `model.norm.weight` | `norm.weight` |

Keep the counts of heads as `Attention`'s `heads` and `kv_heads`, which the next stage reads. Then write `smollm(path)`, SmolLM2 with the file's weights, in evaluation mode. The file keeps each weight as `nn.Linear` does, (outputs, inputs), so none is turned around.

```
SmolLM(vocab, width, hidden, layers, heads, kv_heads)(tokens) -> logits (batch, length, vocab)
smollm(path) -> SmolLM
```

The tests compare your RMSNorm with PyTorch's, your grouped heads with full attention whose key and value heads are copies, and SmolLM2's logits, in float64, with transformers' Llama.
