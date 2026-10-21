"""The help desk's desk: its help pages, searched as Retrieval's fused search searches them, and
the caller's tickets and the advisers' free callback times, which its tools read and change."""

import json
import re
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


class Desk:
    """One caller's desk: their tickets, the advisers' free times by service and day, and the
    tools that read and change them. turn is the caller's message the desk is answering, from
    0, and writes holds each ticket opened and callback booked, with its turn."""

    def __init__(
        self,
        search: Search,
        tickets: list[dict[str, str]],
        free: dict[str, dict[str, list[str]]],
    ) -> None:
        self.search = search
        self.tickets = [dict(ticket) for ticket in tickets]
        self.free = {
            s: {d: list(t) for d, t in days.items()} for s, days in free.items()
        }
        self.turn = 0
        self.writes: list[dict[str, Any]] = []

    def search_help(self, query: str, service: str | None = None) -> dict[str, Any]:
        if service is not None and service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        return {"results": self.search.find(query, service)}

    def list_tickets(self) -> dict[str, Any]:
        return {"tickets": [dict(ticket) for ticket in self.tickets]}

    def open_ticket(self, service: str, summary: str) -> dict[str, Any]:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        if not summary.strip():
            return {"error": "summary is a sentence about the case."}
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
        return {"ticket": ticket}

    def free_callbacks(self, service: str, day: str) -> dict[str, Any]:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        if day not in DAYS:
            return {"error": f"day is one of {', '.join(DAYS)}."}
        return {"day": day, "free": list(self.free[service][day])}

    def book_callback(self, ticket: str, day: str, time: str) -> dict[str, Any]:
        found = [each for each in self.tickets if each["ticket"] == ticket]
        if not found:
            return {"error": f"The caller has no ticket {ticket}."}
        if found[0]["status"] != "open":
            return {"error": f"Ticket {ticket} is closed."}
        service = found[0]["service"]
        if day not in DAYS or time not in self.free[service][day]:
            return {"error": f"The {service} advisers aren't free on {day} at {time}."}
        self.free[service][day].remove(time)
        self.writes.append(
            {
                "tool": "book_callback",
                "ticket": ticket,
                "day": day,
                "time": time,
                "turn": self.turn,
            }
        )
        return {"booked": {"ticket": ticket, "day": day, "time": time}}

    def call(self, name: str, arguments: str) -> str:
        """Runs the tool a model called, with the arguments it gave as JSON text, and gives its
        result as JSON text. A call that can't run gives an error the model can read."""
        tool = TOOLS.get(name)
        if tool is None:
            return json.dumps({"error": f"There is no tool named {name!r}."})
        try:
            given = json.loads(arguments or "{}")
        except json.JSONDecodeError as error:
            return json.dumps({"error": f"The arguments aren't JSON: {error.msg}."})
        if not isinstance(given, dict):
            return json.dumps({"error": "The arguments are a JSON object."})
        properties = tool["parameters"]["properties"]
        missing = [
            key for key in tool["parameters"].get("required", []) if key not in given
        ]
        unknown = [key for key in given if key not in properties]
        if missing or unknown:
            wrong = [f"{key} is missing" for key in missing]
            wrong += [f"{key} isn't one of its arguments" for key in unknown]
            return json.dumps({"error": f"{name}: {'; '.join(wrong)}."})
        if not all(isinstance(value, str) for value in given.values()):
            return json.dumps({"error": f"{name}'s arguments are strings."})
        result = getattr(self, name)(**given)
        return json.dumps(result, ensure_ascii=False)


SERVICE = {"type": "string", "enum": list(SERVICES)}
DAY = {
    "type": "string",
    "enum": list(DAYS),
    "description": "Monday 2026-11-02 to Friday 2026-11-06.",
}
TOOLS: dict[str, dict[str, Any]] = {
    "search_help": {
        "description": "Search the services' help pages. Gives the 5 best passages, each with "
        "its id, its page's title and its text.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for."},
                "service": {
                    **SERVICE,
                    "description": "Search only this service's pages.",
                },
            },
            "required": ["query"],
        },
    },
    "list_tickets": {
        "description": "The caller's tickets, each with its id, service, status and summary.",
        "parameters": {"type": "object", "properties": {}},
    },
    "open_ticket": {
        "description": "Open a ticket for an adviser to look into the caller's case. Gives the "
        "new ticket's id.",
        "parameters": {
            "type": "object",
            "properties": {
                "service": SERVICE,
                "summary": {"type": "string", "description": "One sentence."},
            },
            "required": ["service", "summary"],
        },
    },
    "free_callbacks": {
        "description": "The times a service's advisers are free to call back on a day.",
        "parameters": {
            "type": "object",
            "properties": {"service": SERVICE, "day": DAY},
            "required": ["service", "day"],
        },
    },
    "book_callback": {
        "description": "Book an adviser to call the caller back about one of their open "
        "tickets, at a free time.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket": {"type": "string"},
                "day": DAY,
                "time": {"type": "string", "enum": TIMES},
            },
            "required": ["ticket", "day", "time"],
        },
    },
}


def tools() -> list[dict[str, Any]]:
    """The desk's tools, as a chat request's tools give them."""
    return [
        {"type": "function", "function": {"name": name, **tool}}
        for name, tool in TOOLS.items()
    ]
