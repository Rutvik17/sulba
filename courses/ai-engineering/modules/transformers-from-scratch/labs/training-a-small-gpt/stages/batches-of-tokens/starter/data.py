"""The stories as the model reads them: one stream of tokens, cut into windows."""

import torch
import torch.nn.functional as F

from tokenizer import END, encode


def split(stories):
    """The stories to train on, and every tenth story, the tenth, the twentieth and so on, to
    validate with."""
    raise NotImplementedError


def corpus(stories, merges):
    """The stories' tokens as one tensor, each story followed by the separator."""
    raise NotImplementedError


def batches(tokens, length, size, generator):
    """Batches of size windows, forever, as inputs and targets of length tokens each, the
    targets one token on. Each pass over the tokens takes their windows, length tokens apart from
    the start, in a new order, and leaves out those too few to fill a last batch."""
    raise NotImplementedError


def evaluate(model, tokens, length, size=64):
    """The model's mean loss a token over every window of tokens, length tokens apart from the
    start, read size windows at a time in evaluation mode without gradients."""
    raise NotImplementedError
