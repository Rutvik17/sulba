class Union(Struct):
    """A value that passes any one of its members, as superstruct's union is."""

    type = "union"

    def __init__(self, members):
        self.members = tuple(members)
