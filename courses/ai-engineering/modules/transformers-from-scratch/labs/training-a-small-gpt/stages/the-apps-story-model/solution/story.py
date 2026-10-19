"""The app's story model: a GPT, and its training within the budget."""

import torch

from data import batches
from train import GPT, train

# A model, batches and steps whose multiply-adds stay within the budget: a smaller model that
# reads more tokens beats a larger one that reads fewer.
CONTEXT, WIDTH, LAYERS, HEADS = 128, 128, 2, 4
BATCH, STEPS, PEAK = 16, 900, 3e-3


def make():
    """The app's GPT, untrained, for the stories' vocabulary of 2,048 tokens."""
    torch.manual_seed(0)
    return GPT(2048, CONTEXT, WIDTH, LAYERS, HEADS)


def fit(model, tokens, generator):
    """The model trained on the tokens within the budget, drawing its batches with the
    generator."""
    stream = batches(tokens, model.context, BATCH, generator)
    train(model, stream, STEPS, PEAK, STEPS // 20)
    return model
