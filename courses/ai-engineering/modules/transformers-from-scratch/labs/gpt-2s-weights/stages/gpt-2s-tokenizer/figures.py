import json

import regex

PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
END = "<|endoftext|>"
OPENING, GREETING = "Once upon a time", "こんにちは"


def byte_characters():
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


def pieces(text, ranks):
    """The strings each piece of the text merges into, as GPT-2's tokenizer merges them."""
    characters = byte_characters()
    found = []
    for piece in PATTERN.findall(text):
        parts = [characters[byte] for byte in piece.encode()]
        while len(parts) > 1:
            best = min(
                zip(parts, parts[1:]), key=lambda pair: ranks.get(pair, len(ranks))
            )
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
        found += parts
    return found


def figures():
    with open("data/vocab.json", encoding="utf-8") as file:
        vocabulary = json.load(file)
    with open("data/merges.txt", encoding="utf-8") as file:
        lines = file.read().split("\n")[1:]
    merges = [tuple(line.split(" ")) for line in lines if line]
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    characters = byte_characters()
    kept = sum(chr(byte) == character for byte, character in characters.items())
    opening = pieces(OPENING, ranks)
    greeting = pieces(GREETING, ranks)
    assert len(vocabulary) == 256 + len(merges) + 1 == vocabulary[END] + 1
    return {
        "vocabulary": f"{len(vocabulary):,}",
        "merges": f"{len(merges):,}",
        "bytes": str(len(characters)),
        "end": f"{vocabulary[END]:,}",
        "kept": str(kept),
        "moved": str(256 - kept),
        "space": characters[ord(" ")],
        "newline": characters[ord("\n")],
        "first_merge": "".join(merges[0]),
        "opening": OPENING,
        "opening_tokens": str(len(opening)),
        "opening_strings": ", ".join(opening),
        "greeting": GREETING,
        "greeting_characters": str(len(GREETING)),
        "greeting_bytes": str(len(GREETING.encode())),
        "greeting_tokens": str(len(greeting)),
    }
