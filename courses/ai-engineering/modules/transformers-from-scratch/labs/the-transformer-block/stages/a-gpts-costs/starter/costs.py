"""What a GPT costs, from its configuration alone."""


def costs(vocab, context, width, layers, heads, length):
    """For a GPT built as in stage 3: its parameters, and the multiply-adds of a forward pass
    over length tokens, and of that pass with the backward pass that gives every gradient,
    each divided by length."""
    raise NotImplementedError
