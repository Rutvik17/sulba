"""The stories' tokenizer: byte-pair merges learnt from the stories, and the separator as a
token of its own."""

import regex

# GPT-2's pattern, which splits text into the pieces that merges stay inside: a word with the
# space before it, a number, a run of other marks, or spaces.
PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
# The text that separates the stories in the file.
END = "<|endoftext|>"


def stories(path):
    """The stories in the file at path, each without the spaces and newlines around it. The
    file starts partway through a story, so the text before its first separator is left out."""
    raise NotImplementedError


def train(stories, size):
    """The merges for a vocabulary of size tokens, in the order they're learnt: the 256 bytes
    come first, then a token for each merge, and the separator is the last token. Each merge
    joins the pair of tokens seen side by side most often, and of pairs seen as often, the one
    whose numbers come first."""
    raise NotImplementedError


def encode(text, merges):
    """The text's tokens, with each separator in it as the vocabulary's last token."""
    raise NotImplementedError


def decode(tokens, merges):
    """The text the tokens stand for."""
    raise NotImplementedError
