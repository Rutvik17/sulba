"""The app's stories in batches: every prompt read at once, then a token for every story at
each step."""

import torch
import torch.nn.functional as F

from cache import END, Cache
from rope import rotate
from smollm import THETA


def stories(model, prompts, steps):
    """The tokens model writes after each of prompts, a list of lists of tokens, as generate
    writes them for each prompt alone."""
    raise NotImplementedError
