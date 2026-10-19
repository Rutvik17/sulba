"""The stories' tokenizer: byte-pair merges learnt from the stories, and the separator as a
token of its own."""

from collections import Counter, defaultdict

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
    with open(path, encoding="utf-8") as file:
        pieces = file.read().split(END)
    return [story.strip() for story in pieces[1:] if story.strip()]


def merge(word, pair, new):
    """The word's tokens with each pair, from left to right, made the token new."""
    merged, at = [], 0
    while at < len(word):
        if at + 1 < len(word) and (word[at], word[at + 1]) == pair:
            merged.append(new)
            at += 2
        else:
            merged.append(word[at])
            at += 1
    return merged


def train(stories, size):
    """The merges for a vocabulary of size tokens, in the order they're learnt: the 256 bytes
    come first, then a token for each merge, and the separator is the last token. Each merge
    joins the pair of tokens seen side by side most often, and of pairs seen as often, the one
    whose numbers come first."""
    counts = Counter(piece for story in stories for piece in PATTERN.findall(story))
    words = [list(piece.encode()) for piece in counts]
    weights = list(counts.values())
    # How often each pair is seen, and the pieces it's in, kept up to date as pieces merge.
    pairs = Counter()
    where = defaultdict(set)
    for index, word in enumerate(words):
        for pair in zip(word, word[1:]):
            pairs[pair] += weights[index]
            where[pair].add(index)
    merges = []
    while 256 + len(merges) < size - 1 and pairs:
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        new = 256 + len(merges)
        merges.append(best)
        for index in where.pop(best):
            word, weight = words[index], weights[index]
            for pair in zip(word, word[1:]):
                pairs[pair] -= weight
                if not pairs[pair]:
                    del pairs[pair]
            words[index] = word = merge(word, best, new)
            for pair in zip(word, word[1:]):
                pairs[pair] += weight
                where[pair].add(index)
    return merges


def encode_piece(piece, ranks):
    """A piece's tokens: its bytes, with the pair learnt earliest merged first, until no pair is
    a merge."""
    tokens = list(piece.encode())
    while len(tokens) > 1:
        rank, at = min(
            (ranks.get(pair, len(ranks)), at)
            for at, pair in enumerate(zip(tokens, tokens[1:]))
        )
        if rank == len(ranks):
            break
        tokens[at : at + 2] = [256 + rank]
    return tokens


def encode(text, merges):
    """The text's tokens, with each separator in it as the vocabulary's last token."""
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    end = 256 + len(merges)
    known, tokens = {}, []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(end)
        for piece in PATTERN.findall(part):
            if piece not in known:
                known[piece] = encode_piece(piece, ranks)
            tokens.extend(known[piece])
    return tokens


def decode(tokens, merges):
    """The text the tokens stand for."""
    vocabulary = [bytes([byte]) for byte in range(256)]
    for first, second in merges:
        vocabulary.append(vocabulary[first] + vocabulary[second])
    vocabulary.append(END.encode())
    return b"".join(vocabulary[token] for token in tokens).decode(errors="replace")
