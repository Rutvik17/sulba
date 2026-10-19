"""GPT-2 small and its tokenizer for the app, from the files in a folder."""

import json
import re

import torch

from gpt2 import GPT
from tokenizer import END, PATTERN, byte_characters
from weights import tensors

# Each linear layer's name in GPT-2's file, and its name in the app's GPT.
LINEARS = {
    "attn.c_attn": "attn.qkv",
    "attn.c_proj": "attn.out",
    "mlp.c_fc": "mlp.fc",
    "mlp.c_proj": "mlp.proj",
}


def held(name, tensor):
    """The tensor as the app's GPT holds it: each linear layer's weight turned around."""
    if name.startswith("h.") and tensor.dim() == 2:
        return tensor.reshape(tensor.shape[::-1])
    return tensor


def model(folder):
    """GPT-2 small, with the weights in the folder's model.safetensors, in evaluation mode."""
    gpt = GPT(50257, 1024, 768, 12, 12)
    parameters = dict(gpt.named_parameters())
    with torch.no_grad():
        for name, tensor in tensors(f"{folder}/model.safetensors").items():
            if name.endswith("attn.bias"):
                continue
            for theirs, ours in LINEARS.items():
                name = name.replace(theirs, ours)
            parameter = parameters[re.sub(r"^h\.", "blocks.", name)]
            parameter.copy_(held(name, tensor))
    return gpt.eval()


def tokenizer(folder):
    """GPT-2's vocabulary, each token's number by its string, and its merges' ranks, each
    pair's line in merges.txt, by the pair."""
    with open(f"{folder}/vocab.json", encoding="utf-8") as file:
        vocabulary = json.load(file)
    with open(f"{folder}/merges.txt", encoding="utf-8") as file:
        lines = file.read().split("\n")[1:]
    pairs = [tuple(line.split(" ")) for line in lines if line]
    return vocabulary, {pair: rank for rank, pair in enumerate(pairs)}


def encode(text, tokenizer):
    """The text's tokens, with each END in it as its own token."""
    vocabulary, ranks = tokenizer
    characters = byte_characters()
    tokens = []
    for part in text.split(END):
        for piece in PATTERN.findall(part):
            strings = [characters[byte] for byte in piece.encode()]
            while len(strings) > 1:
                pairs = list(zip(strings, strings[1:]))
                best = min(pairs, key=lambda pair: ranks.get(pair, len(ranks)))
                if best not in ranks:
                    break
                at = pairs.index(best)
                strings[at : at + 2] = [best[0] + best[1]]
            tokens += [vocabulary[string] for string in strings]
        tokens.append(vocabulary[END])
    return tokens


def decode(tokens, tokenizer):
    """The text the tokens stand for."""
    vocabulary, _ = tokenizer
    strings = {number: string for string, number in vocabulary.items()}
    to_byte = {character: byte for byte, character in byte_characters().items()}
    pieces = [bytes(map(to_byte.get, strings[token])) for token in tokens]
    return "".join(piece.decode(errors="replace") for piece in pieces)
