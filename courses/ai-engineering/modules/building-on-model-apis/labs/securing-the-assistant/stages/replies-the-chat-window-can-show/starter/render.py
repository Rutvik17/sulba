"""The model's reply as HTML for the shop's chat window: its text escaped, and its links kept
only when they lead to the shop's own pages."""

# The shop's own hosts. A link to any other host is shown as its text alone.
HOSTS = frozenset({"bikes.example", "www.bikes.example"})


def render(reply: str, hosts: frozenset[str] = HOSTS) -> str:
    """The reply as HTML: a paragraph for each block of lines, <br> between its lines, its bold
    text, and its links to hosts. Everything else is text, and images are left out."""
    raise NotImplementedError
