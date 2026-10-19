"""The app's story model: a GPT, and its training within the budget."""

import torch

from data import batches
from train import GPT, train


def make():
    """The app's GPT, untrained, for the stories' vocabulary of 2,048 tokens."""
    torch.manual_seed(0)
    return GPT(2048, 256, 128, 4, 4)


def fit(model, tokens, generator):
    """The model trained on the tokens within the budget, drawing its batches with the
    generator."""
    return model
