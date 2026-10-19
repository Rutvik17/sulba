class GPT(torch.nn.Module):
    """GPT-2's model: token and position embeddings, the blocks, a final layer
    normalization, and an output layer that is the token embeddings' own weight."""

    def __init__(self, vocab, context, width, layers, heads):
        super().__init__()
        raise NotImplementedError

    def forward(self, tokens):
        """The logits (batch, length, vocab) for tokens (batch, length). Raises ValueError for
        a story longer than the context."""
        raise NotImplementedError
