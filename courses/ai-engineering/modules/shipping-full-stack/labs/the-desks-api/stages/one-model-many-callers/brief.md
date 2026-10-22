Every caller's reply runs on the desk's one model, and a reply can take a minute or more. If every caller is let in at once, every reply gets slower. A caller waiting with no reply is worse off than one told when to come back. In `gate.py`, write the gate in front of the model.

`Gate(running, waiting, seconds)` lets in at most `running` replies at once, keeps at most `waiting` more callers in line, and gives each reply at most `seconds`:

- `enter()` takes a running place at once when one is free. When none is, the caller waits in line until one is, if fewer than `waiting` callers are in line already. Otherwise it raises `Busy(retry_after)`, where `retry_after` is the gate's `seconds` rounded up to a whole number: the time a running reply has before it must end. A caller who leaves while waiting, so that their `enter()` is cancelled, gives up their place in line.
- `leave()` gives a running place back, to the next caller in line.

Then `within(events, seconds)`, an async generator, which gives each event of `events`, an async iterator, until `seconds` have passed since the first was asked for. At that point it raises `TimeoutError`. However it ends, it closes `events` first.

```
Gate(running, waiting, seconds).enter() -> None
Gate(running, waiting, seconds).leave() -> None
within(events, seconds) -> AsyncIterator
```

The tests run on a clock that jumps to the next timer, so a minute's wait takes no time.
