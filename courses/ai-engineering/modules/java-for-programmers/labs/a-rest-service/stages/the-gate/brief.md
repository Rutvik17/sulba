Every caller's reply runs on the desk's one model, and a reply can take a minute or more. As in the desk's Python API, a gate stands in front of the model: it lets only so many replies run at once, keeps a line of callers waiting for a place, and turns the rest away with a time to try again. In `Gate.java`, write it for callers on threads of their own.

`Gate(running, waiting, limit)` lets at most `running` replies run at once, keeps at most `waiting` more callers in line, and gives each reply at most `limit`, a `Duration`:

- `enter()` takes a running place at once when one is free. When none is, the caller waits in line until one is, if fewer than `waiting` callers are in line already. Callers in line get places in the order they came, and a caller who comes as a place frees takes their turn after them.
- When the line is full, `enter()` throws `Gate.Busy`, a checked exception, at once. Its `retryAfter()` is the limit in whole seconds, rounded up: the longest a running reply has before it ends.
- A caller whose thread is interrupted while waiting in line gives up their place in it, and `enter()` throws `InterruptedException`.
- `leave()` gives a running place back, to the next caller in line.
- `limit()` gives the limit.

A gate refuses, with `IllegalArgumentException`, fewer than 1 running place, fewer than 0 places in line, and a limit that isn't longer than no time.

```java
public Gate(int running, int waiting, Duration limit)
public void enter() throws Busy, InterruptedException
public void leave()
public Duration limit()
public static final class Busy extends Exception
public long retryAfter()
```

The tests' callers are virtual threads, and a test sees a caller waiting in line when its thread's state is `WAITING`.
