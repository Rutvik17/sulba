"""Any GPT-2, from its safetensors file."""

import gpt2


def configuration(header):
    """The (vocab, context, width, layers, heads) of the GPT-2 whose safetensors header this is,
    as your header gives it. Raises ValueError when its tensors aren't a GPT-2's."""
    raise NotImplementedError


def load(path):
    """The GPT-2 in the safetensors file at path: a GPT of its configuration, with every
    parameter copied from the file, in evaluation mode. Raises ValueError when the file is
    damaged or its tensors aren't a GPT-2's."""
    raise NotImplementedError
