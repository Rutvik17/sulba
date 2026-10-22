The desk's writes wait for the caller. The model can't open a ticket or book a callback; it proposes one, and the desk makes it once the caller's next message says yes. A proposal is a `Proposal`: the service, the sentence the desk puts to the caller, `says`, and what to make: a ticket with the `summary`, when there's a summary, and a callback on the `ticket`, or on the ticket it opens, on the `day` at the `time`, when there's a day and a time.

`Actions` holds one conversation's tools: the desk's reads and two proposals, which `ACTIONS` describes. `propose_ticket(service, summary)` and `propose(proposal)` are written: `propose` keeps the proposal in `pending`, in place of any before it, and tells the model to ask the caller. In `actions.py`, write:

- `propose_callback(service, day, part=None, time=None, ticket=None, summary=None)`, which looks up what the call needs before it proposes anything. The ticket is the caller's open ticket for the service, or the one they name when they have more than one; with none, the proposal opens a ticket with the summary. The time is the hour asked, or the first free time in the part of the day asked, or the first free time that day. A call that can't be made raises `ToolError` with what to do instead: two open tickets for the service and none named (list them, and ask which), a ticket named that isn't one of them, no open ticket and no summary, or no time that fits (with the times that are free).
- `confirm()`, which makes the pending proposal and says what was done: `Done: ticket T-3001 is open for an adviser.`, or `Done: an adviser will call the caller on Tuesday 2026-11-03 at 09:00 about T-2101.` It checks the time again first, since it may have gone since it was proposed, and a proposal it can't make makes nothing: `The desk couldn't do it: ` and why. With nothing pending: `Nothing was waiting for the caller's yes.`
- `heard(message)`, what the desk did with the caller's message before the model reads it: with a proposal pending, a message that `YES` matches makes it and gives what `confirm` says; any other message drops it and gives `None`.

```
Actions(desk).propose_callback(service, day, part=None, time=None, ticket=None, summary=None) -> str
Actions(desk).confirm() -> str
Actions(desk).heard(message) -> str | None
```
