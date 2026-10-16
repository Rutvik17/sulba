def sample(probabilities, rng):
    """The index of a token drawn with these probabilities, as rng.choice draws it."""
    raise NotImplementedError


def answers(tokens, logits, rng, temperature=1.0, top_k=0, top_p=1.0):
    """The first token of each pair's answer, drawn after warp, in order, from rng."""
    raise NotImplementedError
