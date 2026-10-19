"""The assistant's trainer for the app's model: its stories as tokens, its batches, its
learning rate, and the stories it writes."""

import math

import torch

from tokenizer import END, encode


def corpus(stories, merges):
    """The stories' tokens, one story after another."""
    tokens = []
    for story in stories:
        tokens += encode(story, merges)
    return torch.tensor(tokens)


def batch(tokens, length, size, generator):
    """size windows of length tokens from random places in the stream, with their targets."""
    starts = torch.randint(len(tokens) - length, (size,), generator=generator).tolist()
    inputs = torch.stack([tokens[start : start + length] for start in starts])
    targets = torch.stack([tokens[start : start + length] for start in starts])
    return inputs, targets


def learning_rate(step, steps, peak, warmup):
    """The learning rate at step of a run of steps: up over the warm-up, then down a cosine
    to a tenth of the peak."""
    if step < warmup:
        return peak * (step + 1) / warmup
    progress = (step - warmup) / (steps - 1 - warmup)
    return peak * (0.1 + 0.9 * math.cos(math.pi * progress))


def write(model, tokens, count, generator):
    """The tokens with up to count more drawn from the model, stopping after the
    separator."""
    end = model.wte.num_embeddings - 1
    tokens = list(tokens)
    with torch.no_grad():
        for _ in range(count):
            logits = model(torch.tensor([tokens[: model.context]]))[0, -1]
            chances = torch.softmax(logits, dim=-1)
            tokens.append(torch.multinomial(chances, 1, generator=generator).item())
            if tokens[-1] == end:
                break
    return tokens
