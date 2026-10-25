"""The gate in front of the desk's model: a few replies run at once, a few more wait their turn,
and the rest are told when to come back; and a time limit on each reply."""

import asyncio
from collections.abc import AsyncIterator


class Busy(Exception):
    """Every running place is taken and the queue is full: come back in retry_after seconds."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Busy: come back in {retry_after} seconds.")
        self.retry_after = retry_after


class Gate:
    """At most running replies at once, and at most waiting more in line for a place, each reply
    given at most seconds."""

    def __init__(self, running: int, waiting: int, seconds: float) -> None:
        self.running = running
        self.waiting = waiting
        self.seconds = seconds
        self.places = asyncio.Semaphore(running)
        self.queued = 0

    async def enter(self) -> None:
        """Takes a running place: at once when one is free, after waiting in line when not. A
        caller who would wait past the queue's end gets Busy, to come back once a running reply
        has had its time. A caller who leaves while waiting gives up their place in line."""
        raise NotImplementedError

    def leave(self) -> None:
        """Gives a running place back, for the next caller in line."""
        raise NotImplementedError


async def within[T](events: AsyncIterator[T], seconds: float) -> AsyncIterator[T]:
    """The events, until seconds have passed since the first was asked for: then TimeoutError,
    once the events have been closed."""
    raise NotImplementedError
    yield
