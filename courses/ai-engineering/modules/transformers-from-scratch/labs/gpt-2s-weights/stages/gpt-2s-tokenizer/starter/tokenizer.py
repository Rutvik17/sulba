"""GPT-2's tokenizer, built from its published vocabulary and merges."""

import json

import regex

# GPT-2's pattern, which splits text into the pieces that merges stay inside: a word with the
# space before it, a number, a run of other marks, or spaces.
PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
# The separator between documents, a token of its own.
END = "<|endoftext|>"


def byte_characters():
    """Each byte's character in GPT-2's vocabulary, by the byte: the bytes that print as
    themselves in Latin-1 keep their character, and the others take characters from U+0100 on,
    in the order of the bytes."""
    raise NotImplementedError


def load(folder):
    """GPT-2's vocabulary, each token's number by its string, from vocab.json in folder, and
    its merges, each a pair of strings, in the order merges.txt lists them."""
    raise NotImplementedError


def encode(text, vocabulary, merges):
    """The text's tokens: each END in it as END's token, and each piece of the text between,
    as PATTERN splits it, merged pair by pair, the pair merged first being the one listed
    first."""
    raise NotImplementedError


def decode(tokens, vocabulary):
    """The text the tokens stand for."""
    raise NotImplementedError
