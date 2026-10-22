Callers come back. One who told the desk last week that they can only take calls in the morning shouldn't have to say it again, and one who asks the desk to forget something should find it forgotten.

In `notebook.py`, `Notebook` keeps each caller's notes in a folder between their conversations. `open(caller, system, budget)` gives the memory of a conversation with the caller: a `Memory` that starts with their notes, whose `note(fact)` gives `"Noted."` and keeps the note for their next conversation too, and whose `forget(fact)` forgets one, for the tool `FORGET` describes.

What the desk must do:

- start each conversation with the caller's notes from every one before, in the order they were saved, and keep a note only once;
- never let one caller's notes reach another's conversation, whatever their id, and write nothing outside the notebook's folder;
- forget a note when the caller asks, in this conversation and the next, with `"Forgotten."`, and answer a note it doesn't hold with an error that lists the notes there are;
- hold at most `MOST` notes for a caller, each of at most `LONGEST` characters, and answer a note past either with an error, keeping nothing.

How it does so is yours to choose.

```
Notebook(folder).open(caller, system, budget) -> Memory
memory.note(fact) -> str
memory.forget(fact) -> str
```

Three tests run on every attempt. Then four checks run before the code ships.
