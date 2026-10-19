class MultiHeadAttention(torch.nn.Module):
    """Self-attention in heads: query, key and value layers, attention in each head, and an
    output layer over the heads' outputs side by side."""

    def __init__(self, width, heads):
        """Four nn.Linear layers from width to width: query, key, value and out. Raises
        ValueError if heads doesn't divide width."""
        super().__init__()
        raise NotImplementedError

    def forward(self, x, mask=None):
        """The output (batch, length, width) for x (batch, length, width), and each head's
        weights (batch, heads, length, length). mask is as attention takes it."""
        raise NotImplementedError

    @classmethod
    def from_torch(cls, mha):
        """A MultiHeadAttention with the weights and biases of mha, an nn.MultiheadAttention
        made with batch_first=True."""
        raise NotImplementedError
