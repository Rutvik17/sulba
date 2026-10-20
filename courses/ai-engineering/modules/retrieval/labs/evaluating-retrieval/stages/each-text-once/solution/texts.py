"""The passages a search shows as a reader sees them, each text once."""


def first_passages(texts: dict[str, str]) -> dict[str, str]:
    """Each passage's text, as the first passage in `texts` that holds it."""
    first: dict[str, str] = {}
    for passage, text in texts.items():
        first.setdefault(text, passage)
    return {passage: first[text] for passage, text in texts.items()}


def as_seen(shown: list[str], first: dict[str, str]) -> list[str | None]:
    """The passages shown as a reader sees them, at the same ranks: each as its text's first
    passage, or None if a passage before it showed the same text."""
    seen: set[str] = set()
    texts: list[str | None] = []
    for passage in shown:
        text = first[passage]
        texts.append(None if text in seen else text)
        seen.add(text)
    return texts


def relevant_texts(relevant: set[str], first: dict[str, str]) -> set[str]:
    """The relevant passages' texts, each as its first passage."""
    return {first[passage] for passage in relevant}
