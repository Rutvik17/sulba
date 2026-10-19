FILE = "data/TinyStoriesV2-GPT4-valid.txt"
END = "<|endoftext|>"
# The app's budget of multiply-adds for training, its target on the validation stories, and
# the stories its checks write from the separator: how many, how many must end, and within how
# many tokens. And the stories' vocabulary.
BUDGET, TARGET = 4 * 10**12, 3.2
STORIES, ENDED, LONGEST, VOCAB = 10, 6, 512, 2048
# Models the app might train, as width, blocks and context, the first as make() starts.
MODELS = [(128, 4, 256), (128, 2, 128), (96, 3, 128), (64, 2, 128)]
# Chinchilla's paper: the models it trained, and Chinchilla's and Gopher's sizes and tokens.
TRAINED, CHINCHILLA, TOKENS, GOPHER = 400, 70e9, 1.4e12, 280e9


def parameters(width, layers, context):
    return (
        VOCAB * width
        + context * width
        + layers * (12 * width**2 + 13 * width)
        + 2 * width
    )


def training(width, layers, context):
    """The multiply-adds of training on one token: three times its forward pass."""
    return 3 * (layers * (12 * width**2 + 2 * context * width) + VOCAB * width)


def tex(number):
    mantissa, exponent = f"{number:.0e}".split("e")
    return rf"{mantissa} \times 10^{{{int(exponent)}}}"


def figures():
    with open(FILE, encoding="utf-8") as file:
        told = [story.strip() for story in file.read().split(END)[1:] if story.strip()]
    found = {}
    for number, (width, layers, context) in enumerate(MODELS):
        size = parameters(width, layers, context)
        read = BUDGET // training(width, layers, context)
        found |= {
            f"width_{number}": str(width),
            f"layers_{number}": str(layers),
            f"context_{number}": str(context),
            f"params_{number}": f"{size:,}",
            f"read_{number}": f"{read:,}",
            f"each_{number}": f"{read / size:.0f}"
            if read >= size
            else f"{read / size:.1f}",
        }
    return found | {
        "budget": tex(BUDGET),
        "target": f"{TARGET}",
        "stories": str(STORIES),
        "ended": str(ENDED),
        "longest": str(LONGEST),
        "vocab": f"{VOCAB:,}",
        "training_stories": f"{sum(1 for at in range(len(told)) if at % 10 != 9):,}",
        "chinchilla_trained": str(TRAINED),
        "chinchilla": f"{CHINCHILLA / 1e9:.0f} billion",
        "chinchilla_tokens": f"{TOKENS / 1e12:.1f} trillion",
        "chinchilla_each": f"{TOKENS / CHINCHILLA:.0f}",
        "gopher": f"{GOPHER / 1e9:.0f} billion",
    }
