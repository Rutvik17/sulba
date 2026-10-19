With these settings, a GPT {% $fig.width %} wide with {% $fig.layers %} blocks, {% $fig.params %} parameters, trained for {% $fig.steps %} steps on batches of {% $fig.batch %} windows of {% $fig.context %} tokens: {% $fig.tokens %} tokens in all, at a peak learning rate of {% $fig.peak %} after {% $fig.warmup %} steps of warm-up. On the first {% $fig.measured %} validation tokens, its loss fell from {% $fig.before %} to {% $fig.after %}. Clipping cut the gradient on {% $fig.clipped %} of the {% $fig.steps %} steps.

Asked for a story from the separator before training, it wrote {% $fig.longest %} tokens of this:

> {% $fig.untrained %}

And after:

> {% $fig.trained %}

The words are the stories' words now, and some of their grammar has come, from {% $fig.tokens %} tokens of training.

Weight decay shrinks every parameter it touches toward 0 at every step. For the matrices, the parameters that multiply, that keeps the weights from growing without need. A layer normalization's weight starts at 1, and a bias sits wherever the data puts it, so pulling either toward 0 serves nothing, and training code for GPTs usually leaves them out.

Each token `write` adds runs the whole window through the model again, so writing a token costs about a forward pass of the context.
