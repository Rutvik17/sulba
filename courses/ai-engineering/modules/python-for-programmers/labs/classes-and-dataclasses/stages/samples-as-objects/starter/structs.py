@dataclass
class Sample:
    """One breast mass sample, as the form sends it: its code and three of its mean
    measurements."""

    struct = Object(
        {
            "id": String(),
            "radius": Number(),
            "texture": Number(),
            "smoothness": Number(),
        }
    )

    id: str
    radius: float
    texture: float
    smoothness: float

    @classmethod
    def parse(cls, record):
        """A sample of the record's fields, or a TypeError with the record's first failure,
        explained, as its message."""
        raise NotImplementedError
