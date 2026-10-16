def load_vocabulary(path="data/vocabulary.csv"):
    """The shop's tokenizer: a dict from each token's bytes to its rank."""
    with open(path, encoding="utf-8") as file:
        rows = file.read().splitlines()[1:]
    return {
        bytes.fromhex(token): int(rank)
        for rank, token in (row.split(",") for row in rows)
    }


def encode(text, ranks):
    """text's tokens, as their ranks."""
    raise NotImplementedError


def decode(tokens, ranks):
    """The text the tokens stand for."""
    raise NotImplementedError
