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
    printed = [*range(ord("!"), ord("~") + 1), *range(ord("¡"), ord("¬") + 1)]
    printed += range(ord("®"), ord("ÿ") + 1)
    characters, moved = {}, 0
    for byte in range(256):
        if byte in printed:
            characters[byte] = chr(byte)
        else:
            characters[byte] = chr(256 + moved)
            moved += 1
    return characters


def load(folder):
    """GPT-2's vocabulary, each token's number by its string, from vocab.json in folder, and
    its merges, each a pair of strings, in the order merges.txt lists them."""
    with open(f"{folder}/vocab.json", encoding="utf-8") as file:
        vocabulary = json.load(file)
    with open(f"{folder}/merges.txt", encoding="utf-8") as file:
        lines = file.read().split("\n")[1:]
    return vocabulary, [tuple(line.split(" ")) for line in lines if line]


def merged(piece, ranks):
    """The piece's strings once every merge it allows is made, lowest rank first."""
    parts = list(piece)
    while len(parts) > 1:
        pairs = list(zip(parts, parts[1:]))
        best = min(pairs, key=lambda pair: ranks.get(pair, len(ranks)))
        if best not in ranks:
            break
        joined, at = [], 0
        while at < len(parts):
            if tuple(parts[at : at + 2]) == best:
                joined.append(parts[at] + parts[at + 1])
                at += 2
            else:
                joined.append(parts[at])
                at += 1
        parts = joined
    return parts


def encode(text, vocabulary, merges):
    """The text's tokens: each END in it as END's token, and each piece of the text between,
    as PATTERN splits it, merged pair by pair, the pair merged first being the one listed
    first."""
    characters = byte_characters()
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    tokens = []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(vocabulary[END])
        for piece in PATTERN.findall(part):
            mapped = "".join(characters[byte] for byte in piece.encode())
            tokens.extend(vocabulary[string] for string in merged(mapped, ranks))
    return tokens


def decode(tokens, vocabulary):
    """The text the tokens stand for."""
    strings = {number: string for string, number in vocabulary.items()}
    to_byte = {character: byte for byte, character in byte_characters().items()}
    text = "".join(strings[token] for token in tokens)
    return bytes(to_byte[character] for character in text).decode(errors="replace")
