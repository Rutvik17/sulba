"""What the desk does for the caller: the model proposes a ticket or a callback, after the desk
has looked up what it needs, and the desk makes it only once the caller says yes."""

import re
from dataclasses import dataclass
from typing import Any

from desk import DAYS, EXAMPLES, SERVICE, SERVICES, TIMES, TOOLS, Desk, ToolError, run

YES = re.compile(r"\s*(yes|yeah|yep|sure|ok|okay|please do|go ahead)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Proposal:
    """What the desk will do once the caller says yes: open a ticket for the service with the
    summary, when there's a summary, and book a callback on the ticket, or on the one it opens,
    when there's a day and a time. says is how the desk puts it to the caller."""

    service: str
    says: str
    summary: str | None = None
    ticket: str | None = None
    day: str | None = None
    time: str | None = None


class Actions:
    """One conversation's tools: the desk's reads and the proposals the model can make. A
    proposal waits for the caller's next message, which makes it with a yes and drops it with
    anything else."""

    def __init__(self, desk: Desk) -> None:
        self.desk = desk
        self.pending: Proposal | None = None

    def propose_ticket(self, service: str, summary: str) -> str:
        """Proposes a ticket for an adviser of the service to look into the caller's case."""
        if not summary.strip():
            raise ToolError("summary is a sentence about the caller's case.")
        says = f"open a ticket for a {SERVICES[service]} adviser to look into this: {summary}"
        return self.propose(Proposal(service, says, summary=summary))

    def propose_callback(
        self,
        service: str,
        day: str,
        part: str | None = None,
        time: str | None = None,
        ticket: str | None = None,
        summary: str | None = None,
    ) -> str:
        """Proposes a callback from an adviser of the service on the day, at the time asked, or
        the first free time in the part of the day asked, or that day: on the caller's open
        ticket for the service, or on a new ticket with the summary when they have none."""
        name = SERVICES[service]
        mine = [
            each
            for each in self.desk.tickets
            if each["service"] == service and each["status"] == "open"
        ]
        listed = "; ".join(f"{each['ticket']}, {each['summary']}" for each in mine)
        if ticket is not None and ticket not in [each["ticket"] for each in mine]:
            raise ToolError(
                f"The caller has no open {name} ticket {ticket}. "
                + (f"Their open {name} tickets: {listed}." if mine else "")
            )
        if ticket is None and len(mine) > 1:
            raise ToolError(
                f"The caller has {len(mine)} open {name} tickets: {listed}. Ask which one "
                "the call is about, then call again with ticket."
            )
        if not mine and not (summary or "").strip():
            raise ToolError(
                f"The caller has no open {name} ticket. Call again with summary, a sentence "
                "about what the call is for, and the desk will open one with the callback."
            )
        free = self.desk.free[service][day]
        fits = [
            each
            for each in free
            if (time is None or each == time)
            and (part is None or (each < "12:00") == (part == "morning"))
        ]
        if not free:
            raise ToolError(f"The {name} advisers aren't free on {DAYS[day]} {day}.")
        if not fits:
            asked = f"at {time}" if time else f"in the {part}"
            raise ToolError(
                f"The {name} advisers aren't free {asked} on {DAYS[day]} {day}. They're free "
                f"at {', '.join(free)}."
            )
        when = f"{DAYS[day]} {day} at {fits[0]}"
        if ticket is not None or mine:
            chosen = ticket or mine[0]["ticket"]
            about = next(each["summary"] for each in mine if each["ticket"] == chosen)
            says = f"book a {name} adviser to call the caller on {when} about {chosen}, {about}"
            return self.propose(Proposal(service, says, None, chosen, day, fits[0]))
        says = (
            f"open a ticket for a {name} adviser, {summary}, and book them to call the "
            f"caller on {when}"
        )
        return self.propose(Proposal(service, says, summary, None, day, fits[0]))

    def propose(self, proposal: Proposal) -> str:
        """Keeps the proposal until the caller's next message, in place of any before it."""
        self.pending = proposal
        return (
            f"Proposed: {proposal.says.rstrip('.')}. Ask the caller whether to go ahead. The "
            "desk does it "
            "when they say yes."
        )

    def confirm(self) -> str:
        """Makes the pending proposal, now the caller has said yes, and says what was done."""
        proposal, self.pending = self.pending, None
        if proposal is None:
            return "Nothing was waiting for the caller's yes."
        ticket = proposal.ticket
        try:
            if ticket is None:
                assert proposal.summary is not None
                ticket = self.desk.open_ticket(proposal.service, proposal.summary)
            if proposal.day and proposal.time:
                self.desk.book_callback(ticket, proposal.day, proposal.time)
        except ToolError as error:
            return f"The desk couldn't do it: {error}"
        if proposal.day and proposal.time:
            return (
                f"Done: an adviser will call the caller on {DAYS[proposal.day]} "
                f"{proposal.day} at {proposal.time} about {ticket}."
            )
        return f"Done: ticket {ticket} is open for an adviser."

    def heard(self, message: str) -> str | None:
        """What the desk did with the caller's message before the model reads it: the pending
        proposal made, when the message says yes, or None, after dropping any proposal, when
        it doesn't."""
        if self.pending is None:
            return None
        if YES.match(message):
            return self.confirm()
        self.pending = None
        return None

    def call(self, name: str, arguments: str) -> str:
        """Runs a tool a model called, a read or a proposal, with the arguments it wrote."""
        handlers = {each: getattr(self.desk, each) for each in TOOLS}
        handlers |= {each: getattr(self, each) for each in ACTIONS}
        return run(
            handlers, TOOLS | ACTIONS, EXAMPLES | ACTION_EXAMPLES, name, arguments
        )


DAY = {
    "type": "string",
    "enum": list(DAYS),
    "description": "the date, Monday 2026-11-02 to Friday 2026-11-06.",
}
ACTIONS: dict[str, dict[str, Any]] = {
    "propose_ticket": {
        "description": "Propose a ticket for an adviser to look into the caller's own case. "
        "The desk opens it only once the caller says yes, so ask them after proposing.",
        "parameters": {
            "type": "object",
            "properties": {
                "service": SERVICE,
                "summary": {
                    "type": "string",
                    "description": "one sentence about the case, in the caller's words.",
                },
            },
            "required": ["service", "summary"],
        },
    },
    "propose_callback": {
        "description": "Propose a callback from an adviser, at the hour the caller asks or "
        "the first free one in the part of the day they ask. The desk finds the caller's "
        "open ticket for the service, and opens one with the summary when they have none. "
        "It books the call only once the caller says yes, so ask them after proposing.",
        "parameters": {
            "type": "object",
            "properties": {
                "service": SERVICE,
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
                "ticket": {
                    "type": "string",
                    "description": "the ticket the call is about, if the caller has more "
                    "than one open for the service.",
                },
                "summary": {
                    "type": "string",
                    "description": "one sentence about what the call is for, if the "
                    "caller has no open ticket for the service.",
                },
            },
            "required": ["service", "day"],
        },
    },
}
ACTION_EXAMPLES: dict[str, dict[str, str]] = {
    "propose_ticket": {"service": "dmv", "summary": "My new license hasn't come."},
    "propose_callback": {"service": "ssa", "day": "2026-11-03", "part": "morning"},
}


def tools() -> list[dict[str, Any]]:
    """The desk's reads and proposals, as a chat request's tools give them."""
    return [
        {"type": "function", "function": {"name": name, **spec}}
        for name, spec in (TOOLS | ACTIONS).items()
    ]
