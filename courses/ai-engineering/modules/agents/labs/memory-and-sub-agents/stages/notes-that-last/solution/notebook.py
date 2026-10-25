"""Notes that last: each caller's notes, kept in a folder between their conversations with the
desk, which the caller can ask the desk to forget."""

import hashlib
import json
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


class Kept(Memory):
    """A Memory whose notes are one caller's, read from their file when the conversation starts
    and written to it whenever they change."""

    def __init__(self, path: Path, system: str, budget: int, **options: Any) -> None:
        super().__init__(system, budget, **options)
        self.path = path
        if path.exists():
            self.notes = json.loads(path.read_text(encoding="utf-8"))

    def save(self) -> None:
        """Writes the notes to a file beside the caller's, then puts it in its place, so that
        the caller's file is never left half written."""
        written = self.path.with_suffix(".writing")
        written.write_text(json.dumps(self.notes, ensure_ascii=False), encoding="utf-8")
        written.replace(self.path)

    def note(self, fact: str) -> str:
        fact = fact.strip()
        if not fact:
            return "Error: a note is a sentence about the caller."
        if len(fact) > LONGEST:
            return (
                f"Error: a note has at most {LONGEST} characters, and this one has "
                f"{len(fact)}. Say it in fewer words."
            )
        if fact in self.notes:
            return "Noted already."
        if len(self.notes) >= MOST:
            return (
                f"Error: the caller has {MOST} notes, the most they can have. Forget one "
                "that's no longer true first."
            )
        self.notes.append(fact)
        self.save()
        return "Noted."

    def forget(self, fact: str) -> str:
        fact = fact.strip()
        if fact not in self.notes:
            listed = "; ".join(self.notes) if self.notes else "none"
            return f"Error: there's no note {fact!r}. The caller's notes are: {listed}."
        self.notes.remove(fact)
        self.save()
        return "Forgotten."


class Notebook:
    """Each caller's notes, a file each in folder, named for a hash of the caller's id so that
    no id can name a file outside it or another caller's."""

    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def open(self, caller: str, system: str, budget: int, **options: Any) -> Kept:
        """A conversation's memory for the caller, starting with their notes."""
        name = hashlib.sha256(caller.encode("utf-8")).hexdigest()
        return Kept(self.folder / f"{name}.json", system, budget, **options)
