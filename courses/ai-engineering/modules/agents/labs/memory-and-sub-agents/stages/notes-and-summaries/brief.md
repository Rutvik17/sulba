Clearing has a floor. Once every old result is cleared, the conversation still grows with each message, and then the turns themselves have to go, with what the caller said in them, unless something keeps it.

In `memory.py`, `Memory` extends your `Context` with notes and a summary:

- `note(fact)` keeps a fact the model saves, without the spaces at its ends, and gives `"Noted."`.
- `request()` gives the messages as `Context` does, with the system message after the system prompt listing the notes, `\n\nNotes:\n` then a line `- fact` for each, and after them the summary, `\n\nThe conversation before the messages below, summarised:\n` and the summary.
- `compact(client)` summarises every turn but the last `turns`, a turn being a caller's message and all that follows it, in one request to the model, with `MODEL`, `SAMPLING`, `max_tokens` of 300 and no tools. Its one message is the caller's: `SUMMARISE`, then each caller's message as `Caller: ...` and each of the model's replies that has text as `Assistant: ...`, after `Summary of the conversation before: ...` when there's an earlier summary, all separated by blank lines. Tool calls and results stay out. The reply is the new summary, and those turns are dropped. It gives whether there were turns to summarise.
- `fit(client)` runs before each request. When the last was over the budget, it clears old tool results and gives `"cleared"`, or when there were none left to clear, summarises and gives `"summarised"`. Otherwise it gives `None`.

`Agent` is given: the last lab's tool loop, with its messages in a `Memory`, which it fits before each request and counts after it. It offers the model `NOTE` beside its tools, and runs a call of it with `note`. `REMEMBER` is the line the desk's system prompt gains for it.

```
Memory(system, budget, keep=2, turns=2)
```
