"""The shop's prompts: product titles packed into a prompt within the model's limit, and the
model's reply shown as it streams in."""

import codecs

import tiktoken

from bpe import PATTERN, load_vocabulary

# The special token that ends each title in a prompt.
SEPARATOR = "<|endoftext|>"


def shop_encoding():
    """The shop's tokenizer in tiktoken, with the separator as a special token after its
    vocabulary."""
    ranks = load_vocabulary()
    return tiktoken.Encoding(
        "shop",
        pat_str=PATTERN,
        mergeable_ranks=ranks,
        special_tokens={SEPARATOR: len(ranks)},
    )


def count(text, encoding):
    """The tokens text takes, which the app shows beside each listing."""
    return round(len(text) / 4)


def pack(titles, limit, encoding):
    """The prompt's tokens: as many of the titles as fit within limit tokens, in order, each
    followed by the separator."""
    separator = encoding.encode(SEPARATOR, allowed_special={SEPARATOR})
    tokens, used = [], 0
    for title in titles:
        title_tokens = encoding.encode(title, allowed_special="all")
        if used + len(title_tokens) > limit:
            break
        tokens += title_tokens + separator
        used += len(title_tokens)
    return tokens


def stream(tokens, encoding):
    """The reply's text as each of its tokens arrives, for the app to show."""
    shown = ""
    for token in tokens:
        data = encoding.decode_single_token_bytes(token)
        shown += codecs.decode(data, errors="replace")
        yield shown
