The desk's agent now works through the desk's reads and proposals. Its system prompt, `SYSTEM`, followed by a blank line and the pages the chat was opened from, tells the model to propose a ticket or a callback, ask the caller, and leave the rest to the desk.

In `agent.py`, write `Agent.reply(message)`, the desk's reply to the caller's next message. It sets the desk's `turn` to the number of messages before it, from 0. Before the model reads the message, `self.actions.heard(message)` makes a pending proposal the message says yes to, or drops it. When it made one, the message the model reads is the caller's, a blank line and what the desk did in brackets: `"Yes, please book it.\n\n(The desk: Done: an adviser will call the caller on Tuesday 2026-11-03 at 10:00 about T-2101.)"`. Otherwise the model reads the message as the caller sent it.

Then the tool loop runs as it did in the last lab, with the actions' `tools()`, each call run through `self.actions.call`, at most `rounds` requests a turn, `OutOfRounds` after them, and a `Request` kept for each request in `requests`.

```
Agent(client, desk, page, rounds=8, max_tokens=768).reply(message) -> str
```
