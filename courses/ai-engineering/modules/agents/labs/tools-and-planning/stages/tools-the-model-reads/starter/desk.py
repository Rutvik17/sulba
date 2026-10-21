"""The help desk's desk, with tools written for the model that calls them: results it can cite,
lists that say what they leave out, and errors that say how to call again."""

import json
import re
from collections.abc import Callable
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
        client: httpx.Client,
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

    def find(
        self, query: str, service: str | None = None, k: int = 5
    ) -> list[dict[str, str]]:
        """The k passages that best match the query, best first, of one service's pages or of
        every page, each with its id, its page's title and its text."""
        response = self.client.post(
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

    def search_help(self, query: str, service: str | None = None) -> str:
        """The passages the search finds for the query, each led by the id to cite it by."""
        raise NotImplementedError

    def list_tickets(self, status: str = "open") -> str:
        """The caller's tickets with the status, and how many have the other."""
        raise NotImplementedError

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
            raise ToolError(f"The caller has no callback about {ticket} on {day} at {time}.")
        self.callbacks.remove(booked)
        service = next(each["service"] for each in self.tickets if each["ticket"] == ticket)
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

    def call(self, name: str, arguments: str) -> str:
        """Runs a tool a model called, with the arguments it wrote as JSON text."""
        handlers = {each: getattr(self, each) for each in TOOLS}
        return run(handlers, TOOLS, EXAMPLES, name, arguments)


def run(
    handlers: dict[str, Callable[..., str]],
    specs: dict[str, dict[str, Any]],
    examples: dict[str, dict[str, str]],
    name: str,
    arguments: str,
) -> str:
    """Runs the tool a model called, given its name and the arguments it wrote as JSON text,
    once they fit its spec, and gives its result as text. A call that can't run gives an error
    that says how to call again: from the spec, or the ToolError the tool raises."""
    raise NotImplementedError


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


def tools() -> list[dict[str, Any]]:
    """The desk's tools, as a chat request's tools give them."""
    return [
        {"type": "function", "function": {"name": name, **tool}}
        for name, tool in TOOLS.items()
    ]
