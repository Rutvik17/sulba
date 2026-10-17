class LayerNorm:
    """Layer normalization of each sample, as torch.nn.LayerNorm has it over a sample's
    last axis: the same in training and in evaluation."""

    def __init__(self, normalized_shape, eps=1e-5):
        self.eps = eps
        self.weight = np.ones(normalized_shape)
        self.bias = np.zeros(normalized_shape)

    def forward(self, X, training=True):
        """Each sample of X less its mean over its features, over their standard
        deviation, then scaled by the weight and shifted by the bias."""
        raise NotImplementedError

    def backward(self, dY):
        """The loss's gradient with respect to the batch, given it with respect to the
        outputs, keeping the weight's and the bias's."""
        raise NotImplementedError

    def params(self):
        return [self.weight, self.bias]

    def grads(self):
        return [self.dweight, self.dbias]
