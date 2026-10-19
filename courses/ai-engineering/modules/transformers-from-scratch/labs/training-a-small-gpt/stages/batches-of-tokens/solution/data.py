"""The stories as the model reads them: one stream of tokens, cut into windows."""

import torch
import torch.nn.functional as F

from tokenizer import END, encode


def split(stories):
    """The stories to train on, and every tenth story, the tenth, the twentieth and so on, to
    validate with."""
    training = [story for at, story in enumerate(stories) if at % 10 != 9]
    validation = [story for at, story in enumerate(stories) if at % 10 == 9]
    return training, validation


def corpus(stories, merges):
    """The stories' tokens as one tensor, each story followed by the separator."""
    return torch.tensor(encode(END.join(stories) + END, merges))


def windows(tokens, length, starts):
    """The windows of length + 1 tokens that begin at starts."""
    return tokens[starts[:, None] + torch.arange(length + 1)]


def batches(tokens, length, size, generator):
    """Batches of size windows, forever, as inputs and targets of length tokens each, the
    targets one token on. Each pass over the tokens takes their windows, length tokens apart from
    the start, in a new order, and leaves out those too few to fill a last batch."""
    count = (len(tokens) - 1) // length
    while True:
        order = torch.randperm(count, generator=generator)
        for at in range(0, count - size + 1, size):
            chunk = windows(tokens, length, order[at : at + size] * length)
            yield chunk[:, :-1], chunk[:, 1:]


def evaluate(model, tokens, length, size=64):
    """The model's mean loss a token over every window of tokens, length tokens apart from the
    start, read size windows at a time in evaluation mode without gradients."""
    count = (len(tokens) - 1) // length
    every = windows(tokens, length, torch.arange(count) * length)
    training = model.training
    model.eval()
    total = 0.0
    with torch.no_grad():
        for chunk in every.split(size):
            logits = model(chunk[:, :-1])
            total += F.cross_entropy(
                logits.flatten(0, 1), chunk[:, 1:].flatten(), reduction="sum"
            ).item()
    model.train(training)
    return total / (count * length)
