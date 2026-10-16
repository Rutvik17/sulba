```python
@dataclass(frozen=True, slots=True)
class Sample:
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
        failure = cls.struct.validate(record)
        if failure is not None:
            raise TypeError(failure.explain())
        return cls(**record)
```

`parse` makes the sample with `cls`, the class it was called on, so a subclass's `parse` gives an instance of the subclass, with its methods. A class method that wrote `Sample(...)` would give a `Sample` from any subclass. Python's own types make instances this way too: `dict.fromkeys` is a class method.

`struct` is shared by every sample, as the assistant's list of options was shared by every enums. Sharing suits a struct, which nothing changes once it's made.

A frozen dataclass that compares by its fields gets a `__hash__` from them, so the records the form sends twice make equal samples, which a set holds once. With `slots=True`, a sample has no `__dict__`, and the data model notes that the space saved over one can be significant.
