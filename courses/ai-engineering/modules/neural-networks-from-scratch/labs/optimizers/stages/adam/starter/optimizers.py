class Adam:
    """Adam, as torch.optim.Adam takes its steps: running averages of each gradient and of
    its square, corrected for starting at 0."""

    def __init__(
        self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
    ):
        self.params = params
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        # The steps taken so far, and each parameter's running averages of its gradient
        # and of its gradient squared.
        self.t = 0
        self.m = [np.zeros_like(param) for param in params]
        self.v = [np.zeros_like(param) for param in params]

    def step(self, grads):
        """Moves each parameter one step, given a gradient for each, in the same order."""
        raise NotImplementedError
