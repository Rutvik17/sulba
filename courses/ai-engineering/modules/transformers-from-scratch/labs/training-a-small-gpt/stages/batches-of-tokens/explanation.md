The training stories come to {% $fig.training_tokens %} tokens, and the validation stories to {% $fig.validation_tokens %}. At {% $fig.length %} tokens a window, a pass over the training tokens is {% $fig.windows %} windows: {% $fig.batches %} batches of {% $fig.batch %}, with {% $fig.left %} left out.

Taking each window once a pass, in a new order each time, is how GPT-3 drew its data: it sampled without replacement until it reached the end of a pass. Every token is read before any is read again, and the order changes from pass to pass.

Two losses to measure the model by. Guessing every token as likely as any other gives {% $fig.uniform %}, the natural log of {% $fig.size %}, which is about where a GPT's loss starts, since its first logits are all close to 0. A model that knows only how often each token appears in the training stories, with one added to each count, scores {% $fig.unigram %} on the validation stories. A model that beats it has learnt something of how words follow one another.

Validating on whole stories matters more than it seems. Windows drawn from one stream of every story would put parts of the same story on both sides, and a model can score well on a story it has partly read.
