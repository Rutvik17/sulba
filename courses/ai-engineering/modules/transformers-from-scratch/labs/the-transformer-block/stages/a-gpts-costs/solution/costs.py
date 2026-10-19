"""What a GPT costs, from its configuration alone."""


def costs(vocab, context, width, layers, heads, length):
    """For a GPT built as in stage 3: its parameters, and the multiply-adds of a forward pass
    over length tokens, and of that pass with the backward pass that gives every gradient,
    each divided by length."""
    block = 12 * width**2 + 13 * width
    parameters = vocab * width + context * width + layers * block + 2 * width
    # Each token: the block's layers, its scores and values against length tokens, and the
    # output layer.
    forward = layers * (12 * width**2 + 2 * length * width) + vocab * width
    # Each matrix multiply of the forward pass takes two of its size in the backward pass.
    return {"parameters": parameters, "forward": forward, "training": 3 * forward}
