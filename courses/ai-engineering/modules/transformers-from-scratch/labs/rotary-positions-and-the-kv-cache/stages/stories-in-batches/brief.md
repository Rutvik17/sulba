At bedtime the app writes a story for each child who asks for one, from their own prompt. Written one after another, every story takes a pass of the model for each of its tokens. Written as one batch, each step makes one pass for every story at once.

In `batch.py`, write `stories(model, prompts, steps)`, the tokens `model` writes after each prompt, as your `generate` writes them for that prompt alone: each the likeliest, until it writes `END`, which it keeps, or has written `steps` tokens.

Prompts have different lengths, and a batch is a rectangle, so:

- Pad each prompt on the left to the longest, so that every story's last token sits in the last column.
- A padded place is no token: no row reads it.
- A story's positions count from its own first token, as they would alone.

Then, with the KV cache, read every prompt in one step, and in each step after that, the token each story wrote. Run the model's own parts, as your `step` does. A story that has ended can stay in the batch, but its tokens don't count.

```
stories(model, prompts, steps) -> [[token, ...], ...]
```

Two tests run on every attempt. Then four checks run before the code ships.
