A model doesn't always write its likeliest token. Generation reshapes the probabilities, then draws the next token from them. transformers, Hugging Face's library for running models, applies three settings, in this order:

- **Temperature** `$T$` divides every logit by `$T$` before the softmax. Below 1 it sharpens the probabilities; above 1 it flattens them.
- **Top-k** keeps the `$k$` highest logits, and any tied with the `$k$`-th, and removes the rest.
- **Top-p** keeps the fewest of the likeliest tokens whose probabilities, after temperature and top-k, add up to `$p$` or more, and removes the rest. It always keeps the likeliest token.

Qwen2.5-1.5B-Instruct's generation settings set temperature {% $fig.temperature %}, top-k {% $fig.top_k %} and top-p {% $fig.top_p %}, beside a repetition penalty of {% $fig.penalty %} that lowers the logits of tokens already in the prompt, which this lab leaves out. With top-k at {% $fig.top_k %}, the {% $fig.top %} logits the file keeps for each pair are the only ones these settings let generation draw from.

Write `warp` for one pair's logits:

```
warp(logits, temperature=1.0, top_k=0, top_p=1.0) -> the probabilities generation draws from
```

A removed token has probability 0, and the tokens kept share all of it, in proportion to their probabilities after temperature. `top_k=0` and `top_p=1.0` remove nothing. The tests compare yours with the way transformers applies the settings, on the file's pairs and on random logits.
