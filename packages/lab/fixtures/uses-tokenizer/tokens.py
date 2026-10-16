import regex
import tiktoken

# GPT-2's pattern, which splits text into the pieces a byte-pair encoding merges within.
PATTERN = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""


def pieces(text):
    return regex.findall(PATTERN, text)


def encoding(merges):
    ranks = {bytes([byte]): byte for byte in range(256)}
    for token in merges:
        ranks[token] = len(ranks)
    return tiktoken.Encoding("fixture", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={})
