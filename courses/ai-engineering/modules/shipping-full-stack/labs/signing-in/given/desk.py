"""The help desk, as the Tools and planning lab built it, for an app to serve: the help pages'
search, one caller's tickets, callbacks and the advisers' free times, the tools a model reads
them with, and the tickets and callbacks the model proposes, which the desk makes only once the
caller says yes. The search asks the embedding model through an httpx.AsyncClient."""

import csv
import inspect
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import numpy as np

EMBEDDING = "nomic-embed-text-v1.5"
SERVICES = {
    "ssa": "Social Security",
    "va": "veterans' benefits",
    "studentaid": "federal student aid",
    "dmv": "New York State's DMV",
}
DAYS = {
    "2026-11-02": "Monday",
    "2026-11-03": "Tuesday",
    "2026-11-04": "Wednesday",
    "2026-11-05": "Thursday",
    "2026-11-06": "Friday",
}
TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
WORD = re.compile(r"\w+")


def words(text: str) -> list[str]:
    """A text's words: its runs of letters, digits and _, lowercased."""
    return WORD.findall(text.lower())


class Search:
    """Retrieval's fused search: the passages ranked by BM25 over their words and by their
    vectors' dot product with the query's, fused by reciprocal rank fusion with k = 60, and each
    text given once, by its first passage."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        passages: list[dict[str, str]],
        vectors: np.ndarray,
    ) -> None:
        self.client = client
        self.passages = passages
        self.vectors = vectors.astype(np.float64)
        self.services = np.array([passage["domain"] for passage in passages])
        counts = [words(passage["text"]) for passage in passages]
        self.lengths = np.array([len(each) for each in counts], dtype=np.float64)
        self.terms: list[dict[str, int]] = []
        frequency: dict[str, int] = {}
        for each in counts:
            terms: dict[str, int] = {}
            for word in each:
                terms[word] = terms.get(word, 0) + 1
            self.terms.append(terms)
            for word in terms:
                frequency[word] = frequency.get(word, 0) + 1
        n = len(passages)
        self.idf = {
            word: float(np.log(1 + (n - df + 0.5) / (df + 0.5)))
            for word, df in frequency.items()
        }

    def bm25(self, query: str) -> np.ndarray:
        """Each passage's BM25 score for the query, Lucene's, with k1 = 1.5 and b = 0.75."""
        k1, b = 1.5, 0.75
        norm = k1 * (1 - b + b * self.lengths / self.lengths.mean())
        scores = np.zeros(len(self.passages))
        for word in set(words(query)):
            if word not in self.idf:
                continue
            tf = np.array(
                [terms.get(word, 0) for terms in self.terms], dtype=np.float64
            )
            scores += self.idf[word] * tf / (tf + norm)
        return scores

    async def find(
        self, query: str, service: str | None = None, k: int = 5
    ) -> list[dict[str, str]]:
        """The k passages that best match the query, best first, of one service's pages or of
        every page, each with its id, its page's title and its text."""
        response = await self.client.post(
            "/embeddings", json={"model": EMBEDDING, "input": "search_query: " + query}
        )
        response.raise_for_status()
        vector = np.array(response.json()["data"][0]["embedding"], dtype=np.float64)
        rows = (
            np.flatnonzero(self.services == service)
            if service
            else np.arange(len(self.passages))
        )
        fused = np.zeros(len(rows))
        for scores in (self.bm25(query)[rows], self.vectors[rows] @ vector):
            fused[np.argsort(-scores, kind="stable")] += 1 / (
                60 + np.arange(1, len(rows) + 1)
            )
        seen: set[str] = set()
        found = []
        for row in rows[np.argsort(-fused, kind="stable")].tolist():
            passage = self.passages[row]
            if passage["text"] in seen:
                continue
            seen.add(passage["text"])
            title = passage["title"].split(" | ")[0]
            found.append(
                {"passage": passage["passage"], "page": title, "text": passage["text"]}
            )
            if len(found) == k:
                break
        return found


class ToolError(Exception):
    """A call the desk can't run, with what the model can do instead."""


class Desk:
    """One caller's desk: their tickets and booked callbacks, the advisers' free times by service
    and day, the tools a model reads them with, and the writes the desk makes for the caller.
    turn is the caller's message the desk is answering, from 0, and writes holds each ticket
    opened and callback booked or cancelled, with its turn."""

    def __init__(
        self,
        search: Search,
        tickets: list[dict[str, str]],
        free: dict[str, dict[str, list[str]]],
        callbacks: list[dict[str, str]] | None = None,
    ) -> None:
        self.search = search
        self.tickets = [dict(ticket) for ticket in tickets]
        self.free = {
            s: {d: list(t) for d, t in days.items()} for s, days in free.items()
        }
        self.callbacks = [dict(callback) for callback in callbacks or []]
        self.turn = 0
        self.writes: list[dict[str, Any]] = []

    async def search_help(self, query: str, service: str | None = None) -> str:
        """The passages the search finds for the query, each led by the id to cite it by."""
        found = await self.search.find(query, service)
        where = f"the {SERVICES[service]} pages" if service else "every service's pages"
        shown = "\n\n".join(
            f"[{each['passage']}] {each['page']}\n{each['text']}" for each in found
        )
        return (
            f"{len(found)} passages from {where}, best first. Cite each one you use by its "
            f"id in square brackets, like [{found[0]['passage']}].\n\n{shown}"
        )

    def list_tickets(self, status: str = "open") -> str:
        """The caller's tickets with the status, and how many have the other."""
        mine = [ticket for ticket in self.tickets if ticket["status"] == status]
        other = "closed" if status == "open" else "open"
        rest = sum(ticket["status"] == other for ticket in self.tickets)
        lines = [
            f"{ticket['ticket']}: {SERVICES[ticket['service']]}, {ticket['summary']}"
            for ticket in mine
        ]
        shown = (
            f"The caller's {status} tickets:\n" + "\n".join(lines)
            if lines
            else f"The caller has no {status} tickets."
        )
        if rest:
            shown += (
                f"\nThey have {rest} {other} ticket{'s' if rest > 1 else ''}: "
                f'list_tickets with status "{other}" lists them.'
            )
        return shown

    def open_ticket(self, service: str, summary: str) -> str:
        """Opens a ticket for an adviser of the service, and gives its id."""
        opened = sum(write["tool"] == "open_ticket" for write in self.writes)
        ticket = f"T-{3001 + opened}"
        self.tickets.append(
            {"ticket": ticket, "service": service, "status": "open", "summary": summary}
        )
        self.writes.append(
            {
                "tool": "open_ticket",
                "ticket": ticket,
                "service": service,
                "turn": self.turn,
            }
        )
        return ticket

    def book_callback(self, ticket: str, day: str, time: str) -> None:
        """Books an adviser of the ticket's service at a time they're free."""
        found = [each for each in self.tickets if each["ticket"] == ticket]
        if not found or found[0]["status"] != "open":
            raise ToolError(f"The caller has no open ticket {ticket}.")
        free = self.free[found[0]["service"]][day]
        if time not in free:
            raise ToolError(
                f"The advisers aren't free on {DAYS[day]} {day} at {time}. They're free at "
                f"{', '.join(free) or 'no time that day'}."
            )
        free.remove(time)
        self.callbacks.append({"ticket": ticket, "day": day, "time": time})
        self.writes.append(
            {
                "tool": "book_callback",
                "ticket": ticket,
                "day": day,
                "time": time,
                "turn": self.turn,
            }
        )

    def cancel_callback(self, ticket: str, day: str, time: str) -> None:
        """Cancels a booked callback, and frees its time for the ticket's service."""
        booked = {"ticket": ticket, "day": day, "time": time}
        if booked not in self.callbacks:
            raise ToolError(
                f"The caller has no callback about {ticket} on {day} at {time}."
            )
        self.callbacks.remove(booked)
        service = next(
            each["service"] for each in self.tickets if each["ticket"] == ticket
        )
        self.free[service][day] = sorted([*self.free[service][day], time])
        self.writes.append(
            {
                "tool": "cancel_callback",
                "ticket": ticket,
                "day": day,
                "time": time,
                "turn": self.turn,
            }
        )

    async def call(self, name: str, arguments: str) -> str:
        """Runs a tool a model called, with the arguments it wrote as JSON text."""
        handlers = {each: getattr(self, each) for each in TOOLS}
        return await run(handlers, TOOLS, EXAMPLES, name, arguments)


async def run(
    handlers: dict[str, Callable[..., str | Awaitable[str]]],
    specs: dict[str, dict[str, Any]],
    examples: dict[str, dict[str, str]],
    name: str,
    arguments: str,
) -> str:
    """Runs the tool a model called, given its name and the arguments it wrote as JSON text,
    once they fit its spec, and gives its result as text. A call that can't run gives an error
    that says how to call again: from the spec, or the ToolError the tool raises."""
    spec = specs.get(name)
    if spec is None:
        return (
            f"Error: there is no tool named {name!r}. The tools are {', '.join(specs)}."
        )
    example = json.dumps(examples[name])
    try:
        given = json.loads(arguments or "{}")
    except json.JSONDecodeError as error:
        given = error
    if not isinstance(given, dict):
        return (
            f"Error: {name}'s arguments are one JSON object, like {example}, and these "
            "aren't."
        )
    properties = spec["parameters"]["properties"]
    for key in spec["parameters"].get("required", []):
        if key not in given:
            return (
                f"Error: {name} needs {key}, {properties[key]['description']} For example: "
                f"{example}"
            )
    for key, value in given.items():
        if key not in properties:
            return (
                f"Error: {name} takes no {key}. It takes {', '.join(properties)}, like "
                f"{example}"
            )
        allowed = properties[key].get("enum")
        if not isinstance(value, str) or (allowed and value not in allowed):
            shown = ", ".join(allowed) if allowed else "a string"
            return f"Error: {key} is {shown}, not {json.dumps(value)}."
    try:
        result = handlers[name](**given)
        return await result if inspect.isawaitable(result) else result
    except ToolError as error:
        return f"Error: {error}"


SERVICE = {
    "type": "string",
    "enum": list(SERVICES),
    "description": "the service: ssa, va, studentaid or dmv.",
}
TOOLS: dict[str, dict[str, Any]] = {
    "search_help": {
        "description": "Search the four services' help pages for what the caller asks. "
        "Gives the 5 best passages, each led by its id; cite each one you use by its id in "
        "square brackets, like [p17]. Search one service's pages when the question is about "
        "one service.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "what to search for, in the caller's words.",
                },
                "service": {**SERVICE, "description": "the one service to search."},
            },
            "required": ["query"],
        },
    },
    "list_tickets": {
        "description": "The caller's tickets with a status, open unless you ask for closed "
        "ones, each with its id, service and summary. A callback is booked on an open "
        "ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "closed"],
                    "description": "open or closed.",
                },
            },
        },
    },
}
EXAMPLES: dict[str, dict[str, str]] = {
    "search_help": {"query": "replace a lost card", "service": "ssa"},
    "list_tickets": {"status": "open"},
}


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
        """Makes the pending proposal, now the caller has said yes, and says what was done. The
        time is checked again first, since it may have gone since it was proposed, and a write
        that can't be made makes nothing."""
        proposal, self.pending = self.pending, None
        if proposal is None:
            return "Nothing was waiting for the caller's yes."
        if proposal.day and proposal.time:
            free = self.desk.free[proposal.service][proposal.day]
            if proposal.time not in free:
                return (
                    f"The desk couldn't do it: the {SERVICES[proposal.service]} advisers are no "
                    f"longer free on {DAYS[proposal.day]} {proposal.day} at {proposal.time}. "
                    f"They're free at {', '.join(free) or 'no time that day'}."
                )
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

    async def call(self, name: str, arguments: str) -> str:
        """Runs a tool a model called, a read or a proposal, with the arguments it wrote."""
        handlers: dict[str, Callable[..., str | Awaitable[str]]] = {
            each: getattr(self.desk, each) for each in TOOLS
        }
        handlers |= {each: getattr(self, each) for each in ACTIONS}
        return await run(
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


def load_search(client: httpx.AsyncClient, folder: Path = Path("data")) -> Search:
    """The search over the help pages in the lab's data: each passage in passages.csv, and its
    vector, in the same order, in passage-vectors.csv."""
    with open(folder / "passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    with open(folder / "passage-vectors.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    if [row[0] for row in rows] != [passage["passage"] for passage in passages]:
        raise ValueError("passage-vectors.csv holds other passages than passages.csv.")
    return Search(client, passages, np.array([row[1:] for row in rows], dtype=np.int64))


# The caller the app serves until it has sign-in: their tickets, with the advisers free at every
# hour of every day.
TICKETS = [
    {
        "ticket": "T-2041",
        "service": "ssa",
        "status": "open",
        "summary": "My replacement Social Security card hasn't come.",
    },
    {
        "ticket": "T-1873",
        "service": "dmv",
        "status": "closed",
        "summary": "My new address isn't on my license.",
    },
]


def free_times() -> dict[str, dict[str, list[str]]]:
    """Every hour of every day, free for each service's advisers."""
    return {service: {day: list(TIMES) for day in DAYS} for service in SERVICES}
