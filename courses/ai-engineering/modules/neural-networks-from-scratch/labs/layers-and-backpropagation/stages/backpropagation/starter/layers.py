class Network:
    """Layers run in order: the forward pass through each in turn, and the backward pass
    back through them in reverse."""

    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        """The logits for a batch X: X through each layer in turn."""
        raise NotImplementedError

    def backward(self, dlogits):
        """Runs the loss's gradient with respect to the logits back through the layers,
        each layer's backward pass handing its result to the layer before, and returns the
        gradient with respect to the network's inputs."""
        raise NotImplementedError

    def step(self, lr):
        """Moves each linear layer's weight and bias down its gradient, lr times it."""
        raise NotImplementedError


def linear_layer(inputs, outputs, rng):
    """A Linear layer started as PyTorch's nn.Linear starts one: each weight and bias
    drawn uniformly from -1/sqrt(inputs) to 1/sqrt(inputs) with rng, the weight first."""
    raise NotImplementedError
