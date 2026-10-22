A caller can ask to move a callback they've booked. The desk's agent can move one with two more tools, which `MOVES` describes: `list_callbacks`, a read, and `propose_move`, a proposal. In `moves.py`, `Moves` extends your `Actions` with them:

- `list_callbacks()` gives `The caller's booked callbacks:` and a line for each, its day, time, ticket, service and summary, such as `Tuesday 2026-11-03 at 10:00: T-2101, Social Security, Replacement card`, or `The caller has no callbacks booked.`
- `propose_move(ticket, day, part=None, time=None)` proposes moving the call booked about the ticket to the day, at the hour asked, or the first free time in the part of the day asked, or that day, and keeps the move, a `Move`, as the pending proposal.
- `confirm()` makes the pending move, as `Actions.confirm` makes any other proposal, and says what was done: `Done: the call about T-2101 is now on Thursday 2026-11-05 at 13:00.`

What the desk must do:

- move nothing until the caller says yes;
- never leave the caller without a call, from a move or from one that fails;
- keep the call where it was when the new time has gone by the yes, and say the times that are free;
- refuse a move of a call the caller hasn't booked, or to a time that isn't free, with what they can ask for instead.

How it does so is yours to choose.

```
Moves(desk).list_callbacks() -> str
Moves(desk).propose_move(ticket, day, part=None, time=None) -> str
Moves(desk).confirm() -> str
```

Three tests run on every attempt. Then four checks run before the code ships.
