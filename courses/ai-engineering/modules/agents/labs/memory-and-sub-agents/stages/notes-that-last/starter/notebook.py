"""Notes that last: each caller's notes, kept in a folder between their conversations with the
desk, which the caller can ask the desk to forget."""

from pathlib import Path
from typing import Any

from memory import Memory

# The most notes a caller holds, and the most characters a note has.
MOST = 20
LONGEST = 200
FORGET = {
    "type": "function",
    "function": {
        "name": "forget",
        "description": "Forget one of the caller's notes, when they ask you to or it's no "
        "longer true. Give the note as the notes list it.",
        "parameters": {
            "type": "object",
            "properties": {"fact": {"type": "string", "description": "The note."}},
            "required": ["fact"],
        },
    },
}


class Notebook:
    """Each caller's notes, kept in folder between their conversations."""

    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)

    def open(self, caller: str, system: str, budget: int, **options: Any) -> Memory:
        """A conversation's memory for the caller, starting with their notes: a Memory whose
        note and forget keep the caller's notes for their next conversation."""
        raise NotImplementedError
