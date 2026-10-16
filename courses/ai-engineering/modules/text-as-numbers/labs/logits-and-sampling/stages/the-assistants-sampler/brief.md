The shop needs far more pairs labelled than people can label, and wants the judge to label them as the model would answer at its own settings. It asked an assistant for the code. The assistant wrote `sampler.py`: `warp` reshapes a pair's logits with Qwen2.5-1.5B-Instruct's settings, `sample` draws a token, and `label` gives each pair the first token of its answer, from a fixed seed so that every run gives the same labels. Its five tests all pass.

Review it as if it were about to label the shop's catalogue: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- apply the temperature to the logits, as generation does;
- keep the tokens top-p keeps, the one that takes the total to `$p$` among them;
- draw each kept token with its probability;
- draw each pair's token with a random number of its own, and give the same labels on every run.
