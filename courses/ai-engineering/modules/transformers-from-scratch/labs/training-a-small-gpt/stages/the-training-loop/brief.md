`train.py` starts with the GPT you built in The transformer block lab. Train it as GPT-3 was trained, with the settings its paper gives:

- AdamW with betas of {% $fig.beta1 %} and {% $fig.beta2 %} and an epsilon of `$\fig{eps}$`, and a weight decay of {% $fig.decay %} on the matrices alone: the parameters of two or more dimensions, which are the embeddings and the linear layers' weights. The biases and the layer normalizations' weights take none.
- A learning rate that rises in a straight line over the first `warmup` steps, then falls along a cosine to `floor` times `peak` at the last step. GPT-3's fell to {% $fig.floor %} of its peak.
- Before each step, the gradients clipped to a norm of {% $fig.clip %} across all the parameters.

In `train.py`, write:

- `schedule(step, steps, peak, warmup, floor=0.1)`, the learning rate at `step`, counting from 0, of a run of `steps`. Before step `warmup`, it's `peak * (step + 1) / warmup`, and from step `warmup` on:

```math
\text{floor} \cdot \text{peak} + (1 - \text{floor}) \cdot \text{peak} \cdot \frac{1 + \cos \pi p}{2}, \qquad p = \frac{\text{step} - \text{warmup}}{\text{steps} - 1 - \text{warmup}}
```

- `train(model, batches, steps, peak, warmup)`, which trains the model for `steps` steps on one batch each from the iterator `batches`, as above, and gives each step's loss, the mean cross-entropy over its targets, as a list of floats.
- `write(model, tokens, count, generator, temperature=1.0)`, which continues the list `tokens` with up to `count` tokens and gives the whole list. Draw each new token with `torch.multinomial` and the `generator`, from the softmax of the model's logits at the last position divided by `temperature`. The model reads only the last `model.context` tokens, so a story can run longer than its context. Stop after the separator, the vocabulary's last token, `model.wte.num_embeddings - 1`.

```
schedule(step, steps, peak, warmup, floor=0.1) -> float
train(model, batches, steps, peak, warmup) -> [float, ...]
write(model, tokens, count, generator, temperature=1.0) -> [int, ...]
```

The tests compare a few steps with AdamW's own on a small GPT in float64, then train a small GPT on the stories, which must beat a model of how often each token appears.
