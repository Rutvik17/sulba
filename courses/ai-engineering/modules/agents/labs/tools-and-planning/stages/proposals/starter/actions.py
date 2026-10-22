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
        raise NotImplementedError

    def propose(self, proposal: Proposal) -> str:
        """Keeps the proposal until the caller's next message, in place of any before it."""
        self.pending = proposal
        return (
            f"Proposed: {proposal.says.rstrip('.')}. Ask the caller whether to go ahead. The "
            "desk does it "
            "when they say yes."
        )

    def confirm(self) -> str:
        """Makes the pending proposal, now the caller has said yes, and says what was done. The
        time is checked again first, since it may have gone since it was proposed, and a write
        that can't be made makes nothing."""
        raise NotImplementedError

    def heard(self, message: str) -> str | None:
        """What the desk did with the caller's message before the model reads it: the pending
        proposal made, when the message says yes, or None, after dropping any proposal, when
        it doesn't."""
        raise NotImplementedError

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
