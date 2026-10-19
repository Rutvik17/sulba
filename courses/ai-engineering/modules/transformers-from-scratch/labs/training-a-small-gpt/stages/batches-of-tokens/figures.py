import math
from collections import Counter, defaultdict

import regex
import torch

PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
END = "<|endoftext|>"
FILE = "data/TinyStoriesV2-GPT4-valid.txt"
# The lab's vocabulary, and a window and a batch as the app's model might read them.
SIZE, LENGTH, BATCH = 2048, 256, 16


def train(texts, size):
    """The merges, as stage 1's solution learns them."""
    counts = Counter(piece for text in texts for piece in PATTERN.findall(text))
    words = [list(piece.encode()) for piece in counts]
    weights = list(counts.values())
    pairs, where = Counter(), defaultdict(set)
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
            merged, at = [], 0
            while at < len(word):
                if at + 1 < len(word) and (word[at], word[at + 1]) == best:
                    merged.append(new)
                    at += 2
                else:
                    merged.append(word[at])
                    at += 1
            words[index] = merged
            for pair in zip(merged, merged[1:]):
                pairs[pair] += weight
                where[pair].add(index)
    return merges


def encode(text, merges):
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    known, tokens = {}, []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(256 + len(merges))
        for piece in PATTERN.findall(part):
            if piece not in known:
                word = list(piece.encode())
                while len(word) > 1:
                    rank, place = min(
                        (ranks.get(pair, len(ranks)), place)
                        for place, pair in enumerate(zip(word, word[1:]))
                    )
                    if rank == len(ranks):
                        break
                    word[place : place + 2] = [256 + rank]
                known[piece] = word
            tokens.extend(known[piece])
    return tokens


def figures():
    with open(FILE, encoding="utf-8") as file:
        told = [story.strip() for story in file.read().split(END)[1:] if story.strip()]
    training = [story for at, story in enumerate(told) if at % 10 != 9]
    validation = [story for at, story in enumerate(told) if at % 10 == 9]
    merges = train(training, SIZE)
    learnt = torch.tensor(encode(END.join(training) + END, merges))
    held = torch.tensor(encode(END.join(validation) + END, merges))
    windows = (len(learnt) - 1) // LENGTH
    # A model that knows only how often each token appears in the training stories, with one
    # added to each count, so a token they never hold still has a chance.
    counts = torch.bincount(learnt, minlength=SIZE).double()
    shares = (counts + 1) / (counts.sum() + SIZE)
    unigram = -shares.log()[held].mean().item()
    return {
        "training": f"{len(training):,}",
        "validation": f"{len(validation):,}",
        "training_tokens": f"{len(learnt):,}",
        "validation_tokens": f"{len(held):,}",
        "length": str(LENGTH),
        "windows": f"{windows:,}",
        "batch": str(BATCH),
        "batches": f"{windows // BATCH:,}",
        "left": str(windows % BATCH),
        "size": f"{SIZE:,}",
        "uniform": f"{math.log(SIZE):.2f}",
        "unigram": f"{unigram:.2f}",
    }
