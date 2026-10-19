# GPT-2's vocabulary and context, and its four sizes as (width, layers, heads).
VOCAB, CONTEXT = 50257, 1024
SIZES = {
    "small": (768, 12, 12),
    "medium": (1024, 24, 16),
    "large": (1280, 36, 20),
    "xl": (1600, 48, 25),
}
STD = 0.02


def parameters(width, layers):
    """Token and position embeddings, the blocks, and the final layer normalization."""
    return (
        VOCAB * width
        + CONTEXT * width
        + layers * (12 * width**2 + 13 * width)
        + 2 * width
    )


def figures():
    width, layers, _ = SIZES["small"]
    found = {
        f"{name}_params": f"{parameters(w, n):,}" for name, (w, n, _) in SIZES.items()
    }
    found.update({f"{name}_layers": str(n) for name, (_, n, _) in SIZES.items()})
    found.update({f"{name}_width": f"{w:,}" for name, (w, _, _) in SIZES.items()})
    tied = VOCAB * width
    return {
        **found,
        "vocab": f"{VOCAB:,}",
        "context": f"{CONTEXT:,}",
        "std": f"{STD:g}",
        "tied": f"{tied:,}",
        "tied_share": f"{tied / parameters(width, layers):.0%}",
        "residual": str(2 * layers),
        "deep_std": f"{STD / (2 * layers) ** 0.5:.5f}",
    }
