# GPT-2 small: a vocabulary of 50,257, a context of 1,024, 12 blocks of 768 in 12 heads.
GPT2 = (50257, 1024, 768, 12, 12)
# GPT-3's largest model, from Table 2.1 of its paper: 96 blocks of 12,288 in 96 heads, with a
# context of 2,048 and GPT-2's vocabulary.
GPT3 = (50257, 2048, 12288, 96, 96)


def parameters(vocab, context, width, layers, heads):
    return (
        vocab * width
        + context * width
        + layers * (12 * width**2 + 13 * width)
        + 2 * width
    )


def forward(vocab, context, width, layers, heads, length):
    return layers * (12 * width**2 + 2 * length * width) + vocab * width


def figures():
    _, context, width, layers, heads = GPT2
    return {
        "context": f"{context:,}",
        "small": f"{parameters(*GPT2):,}",
        "small_forward": f"{forward(*GPT2, context):,}",
        "small_training": f"{3 * forward(*GPT2, context):,}",
        "gpt3_layers": str(GPT3[3]),
        "gpt3_width": f"{GPT3[2]:,}",
        "gpt3_context": f"{GPT3[1]:,}",
        "gpt3": f"{parameters(*GPT3):,}",
    }
