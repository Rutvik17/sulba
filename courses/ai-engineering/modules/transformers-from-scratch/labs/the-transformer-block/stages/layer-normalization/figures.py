# GPT-2 small: 12 blocks of 768, each with two layer normalizations, and one more at the end.
# Its configuration sets their epsilon to 1e-5.
WIDTH, LAYERS, EPS = 768, 12, 1e-5


def figures():
    norms = 2 * LAYERS + 1
    return {
        "eps": f"{EPS:g}",
        "norms": str(norms),
        "layers": str(LAYERS),
        "width": str(WIDTH),
        "params": f"{norms * 2 * WIDTH:,}",
    }
