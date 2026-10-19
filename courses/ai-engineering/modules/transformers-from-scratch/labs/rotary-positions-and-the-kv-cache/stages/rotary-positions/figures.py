import math

# SmolLM2-135M's settings, from its config.json at the lab's revision: the width of each head,
# its rotary base and its longest context. The tokens it was trained on, from its model card.
DIM, THETA, CONTEXT = 64, 100000.0, 8192
TRAINED = "2 trillion"
# GPT-2 small's learnt positions: its context and its width.
GPT2_CONTEXT, GPT2_WIDTH = 1024, 768


def figures():
    pairs = DIM // 2
    slowest = THETA ** (-2 * (pairs - 1) / DIM)
    period = 2 * math.pi / slowest
    assert abs(period % 1 - 0.5) > 0.01
    return {
        "trained_tokens": TRAINED,
        "dim": str(DIM),
        "pairs": str(pairs),
        "theta": f"{THETA:,.0f}",
        "context": f"{CONTEXT:,}",
        "last": f"{CONTEXT - 1:,}",
        "fastest_period": f"{2 * math.pi:.1f}",
        "slowest_period": f"{period:,.0f}",
        "gpt2_positions": f"{GPT2_CONTEXT * GPT2_WIDTH:,}",
    }
