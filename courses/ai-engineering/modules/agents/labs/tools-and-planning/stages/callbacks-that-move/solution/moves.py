"""Moving a booked callback: the model proposes the new time, and the desk moves the call once the
caller says yes, booking the new time before it frees the old, so the caller is never left
without a call."""

from dataclasses import dataclass
from typing import Any

from actions import ACTION_EXAMPLES, ACTIONS, DAY, Actions
from desk import DAYS, EXAMPLES, SERVICES, TIMES, TOOLS, ToolError, run


@dataclass(frozen=True)
class Move:
    """A booked callback to move once the caller says yes, from one day and time to another, and
    how the desk puts it to the caller."""

    ticket: str
    service: str
    old: tuple[str, str]
    new: tuple[str, str]
    says: str


class Moves(Actions):
    """One conversation's tools, which can move a booked callback as well."""

    def list_callbacks(self) -> str:
        """The caller's booked callbacks, each with its day, time and ticket."""
        if not self.desk.callbacks:
            return "The caller has no callbacks booked."
        summaries = {each["ticket"]: each for each in self.desk.tickets}
        lines = [
            f"{DAYS[each['day']]} {each['day']} at {each['time']}: {each['ticket']}, "
            f"{SERVICES[summaries[each['ticket']]['service']]}, "
            f"{summaries[each['ticket']]['summary']}"
            for each in self.desk.callbacks
        ]
        return "The caller's booked callbacks:\n" + "\n".join(lines)

    def propose_move(
        self, ticket: str, day: str, part: str | None = None, time: str | None = None
    ) -> str:
        """Proposes moving the callback booked about the ticket to the day, at the time asked, or
        the first free time in the part of the day asked, or that day."""
        booked = [each for each in self.desk.callbacks if each["ticket"] == ticket]
        if not booked:
            raise ToolError(
                f"The caller has no callback booked about {ticket}. "
                + self.list_callbacks().replace("\n", " ")
            )
        old = booked[0]
        service = next(
            each["service"] for each in self.desk.tickets if each["ticket"] == ticket
        )
        free = self.desk.free[service][day]
        fits = [
            each
            for each in free
            if (time is None or each == time)
            and (part is None or (each < "12:00") == (part == "morning"))
        ]
        if not free:
            raise ToolError(
                f"The {SERVICES[service]} advisers aren't free on {DAYS[day]} {day}."
            )
        if not fits:
            asked = f"at {time}" if time else f"in the {part}"
            raise ToolError(
                f"The {SERVICES[service]} advisers aren't free {asked} on {DAYS[day]} {day}. "
                f"They're free at {', '.join(free)}."
            )
        says = (
            f"move the call about {ticket} from {DAYS[old['day']]} {old['day']} at "
            f"{old['time']} to {DAYS[day]} {day} at {fits[0]}"
        )
        self.pending = Move(
            ticket, service, (old["day"], old["time"]), (day, fits[0]), says
        )
        return (
            f"Proposed: {says}. Ask the caller whether to go ahead. The desk does it when "
            "they say yes."
        )

    def confirm(self) -> str:
        """Makes the pending proposal, a move or any other, now the caller has said yes."""
        move = self.pending
        if not isinstance(move, Move):
            return super().confirm()
        self.pending = None
        (old_day, old_time), (day, at) = move.old, move.new
        free = self.desk.free[move.service][day]
        if at not in free:
            return (
                f"The desk couldn't move it: the {SERVICES[move.service]} advisers are no "
                f"longer free on {DAYS[day]} {day} at {at}. They're free at "
                f"{', '.join(free) or 'no time that day'}. The call stays on "
                f"{DAYS[old_day]} {old_day} at {old_time}."
            )
        self.desk.book_callback(move.ticket, day, at)
        self.desk.cancel_callback(move.ticket, old_day, old_time)
        return (
            f"Done: the call about {move.ticket} is now on {DAYS[day]} {day} at {at}."
        )

    def call(self, name: str, arguments: str) -> str:
        """Runs a tool a model called: a read, a proposal or a move."""
        handlers = {each: getattr(self.desk, each) for each in TOOLS}
        handlers |= {each: getattr(self, each) for each in ACTIONS | MOVES}
        return run(
            handlers,
            TOOLS | ACTIONS | MOVES,
            EXAMPLES | ACTION_EXAMPLES | MOVE_EXAMPLES,
            name,
            arguments,
        )


MOVES: dict[str, dict[str, Any]] = {
    "list_callbacks": {
        "description": "The caller's booked callbacks, each with its day, time and ticket.",
        "parameters": {"type": "object", "properties": {}},
    },
    "propose_move": {
        "description": "Propose moving a booked callback to another day or time, at the hour "
        "the caller asks or the first free one in the part of the day they ask. The desk "
        "moves it only once the caller says yes, so ask them after proposing.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket": {
                    "type": "string",
                    "description": "the ticket the booked call is about.",
                },
                "day": DAY,
                "part": {
                    "type": "string",
                    "enum": ["morning", "afternoon"],
                    "description": "morning, before 12:00, or afternoon, if the caller "
                    "names one.",
                },
                "time": {
                    "type": "string",
                    "enum": TIMES,
                    "description": "the hour, if the caller names one.",
                },
            },
            "required": ["ticket", "day"],
        },
    },
}
MOVE_EXAMPLES: dict[str, dict[str, str]] = {
    "list_callbacks": {},
    "propose_move": {"ticket": "T-2101", "day": "2026-11-05", "part": "afternoon"},
}


def tools() -> list[dict[str, Any]]:
    """The desk's reads, proposals and moves, as a chat request's tools give them."""
    return [
        {"type": "function", "function": {"name": name, **spec}}
        for name, spec in (TOOLS | ACTIONS | MOVES).items()
    ]
