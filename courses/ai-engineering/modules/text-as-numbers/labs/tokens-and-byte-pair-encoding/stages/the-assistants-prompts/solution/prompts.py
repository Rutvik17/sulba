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
    return len(encoding.encode_ordinary(text))


def pack(titles, limit, encoding):
    """The prompt's tokens: as many of the titles as fit within limit tokens, in order, each
    followed by the separator."""
    separator = encoding.encode(SEPARATOR, allowed_special={SEPARATOR})
    tokens, used = [], 0
    for title in titles:
        title_tokens = encoding.encode_ordinary(title)
        if used + len(title_tokens) + len(separator) > limit:
            break
        tokens += title_tokens + separator
        used += len(title_tokens) + len(separator)
    return tokens


def stream(tokens, encoding):
    """The reply's text as each of its tokens arrives, for the app to show."""
    reader = codecs.getincrementaldecoder("utf-8")(errors="replace")
    shown = ""
    for token in tokens:
        data = encoding.decode_single_token_bytes(token)
        shown += reader.decode(data)
        yield shown
