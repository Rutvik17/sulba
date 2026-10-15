class StrengthModel:
    """The model chosen on the validation mixes and fit on the training mixes, which
    refuses a mix outside the ranges it was fit on."""

    def __init__(self, train, validation):
        """Chooses the degree and penalty on the validation mixes, fits on the training
        mixes, and keeps each measurement's lowest and highest value in them."""
        raise NotImplementedError

    def accepts(self, mixes):
        """Whether each mix has every measurement inside the training mixes' ranges."""
        raise NotImplementedError

    def predict(self, mixes):
        """The strength in MPa of each mix. Raises ValueError if any mix isn't accepted."""
        raise NotImplementedError
