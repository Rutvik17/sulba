class AdamW(Adam):
    """AdamW, as torch.optim.AdamW takes its steps: Adam with the weight decay taken out of
    the gradient, so that it shrinks each weight directly."""

    def __init__(
        self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01
    ):
        raise NotImplementedError
