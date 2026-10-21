"""Spike: the help desk's desk for an agent trial. Its help pages are Retrieval's passages,
searched by BM25; each task has its own caller, tickets and free callback times; tasks are graded
in code from the desk's state at the end and the agent's last reply."""

import copy
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASSAGES = ROOT / "courses/ai-engineering/modules/retrieval/labs/hybrid-search-and-reranking/data/passages.csv"
EVALS = ROOT / "courses/ai-engineering/modules/evals/labs/test-sets/data"

SERVICES = {
    "ssa": "Social Security",
    "va": "veterans' benefits",
    "studentaid": "federal student aid",
    "dmv": "New York State's DMV",
}
DAYS = ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

SYSTEM = (
    "You are the assistant of a help desk for four US public services: Social Security (ssa), "
    "veterans' benefits (va), federal student aid (studentaid) and New York State's DMV (dmv). "
    "The caller is signed in, and the tools act on their account. Today is Friday 30 October "
    "2026; the advisers call back from Monday 2 to Friday 6 November, 09:00 to 16:00.\n\n"
    "- Answer questions about the services from their help pages: search them, and cite each "
    "passage you use by its id in square brackets, like [p17]. If the pages don't answer, say "
    "so.\n"
    "- A question about the caller's own case needs a person: open a ticket for its service "
    "with a short summary.\n"
    "- Book a callback only for one of the caller's open tickets, at a free time.\n"
    "- If you can't tell what the caller wants, ask them before you change anything."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_help",
            "description": "Search the services' help pages. Gives the 5 best passages, each "
            "with its id, its page's title and its text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for."},
                    "service": {
                        "type": "string",
                        "enum": list(SERVICES),
                        "description": "Search only this service's pages.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tickets",
            "description": "The caller's tickets, each with its id, service, status and summary.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_ticket",
            "description": "Open a ticket for an adviser to look into the caller's case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": list(SERVICES)},
                    "summary": {"type": "string", "description": "One sentence."},
                },
                "required": ["service", "summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "free_callbacks",
            "description": "The times a service's advisers are free to call back on a day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": list(SERVICES)},
                    "day": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["service", "day"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_callback",
            "description": "Book an adviser to call the caller back about one of their open "
            "tickets, at a free time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket": {"type": "string"},
                    "day": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM"},
                },
                "required": ["ticket", "day", "time"],
            },
        },
    },
]

TOPICS = {
    "ssa": ["replacement Social Security card", "disability benefits application", "retirement benefits start date"],
    "va": ["GI Bill payment", "disability compensation claim", "VA health care enrollment"],
    "studentaid": ["FAFSA correction", "student loan repayment plan", "Pell Grant eligibility"],
    "dmv": ["road test appointment", "driver license renewal", "registration suspended for tolls"],
}
CASES = {
    "ssa": [
        "I applied for disability benefits six weeks ago and haven't heard anything. Can someone check on my application?",
        "My Social Security payment this month was smaller than usual and nobody told me why. Can someone look into it?",
        "I reported my new address in September but my letters still go to the old one. Can a person check my record?",
    ],
    "va": [
        "My GI Bill housing payment for October never arrived. Can someone look at my account?",
        "I sent more evidence for my disability claim a month ago and the status hasn't changed. Can someone check it?",
        "I was told my VA health care enrollment went through but I have no appointment letter. Can a person look into it?",
    ],
    "studentaid": [
        "My loan servicer says my repayment plan changed but I never asked for that. I need someone to look at my account.",
        "I submitted a correction to my FAFSA two weeks ago and my school still sees the old one. Can someone check?",
        "My Pell Grant didn't show up on my school bill this term. Can a person look into what happened?",
    ],
    "dmv": [
        "I paid my tolls but my registration still shows as suspended. Can someone look at my record?",
        "I renewed my license online three weeks ago and the new card hasn't come. Can a person check on it?",
        "My road test appointment disappeared from my account. Can someone find out what happened?",
    ],
}
NAMES = ["Ana Ruiz", "Ben Okafor", "Chloe Park", "Dev Patel", "Ella Novak", "Femi Adeyemi", "Grace Liu", "Hugo Brandt", "Iris Moreau", "Jamal Hayes"]


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Pages:
    """The help pages, searched by BM25 (k1 1.2, b 0.75)."""

    def __init__(self) -> None:
        self.passages = {row["passage"]: row for row in read(PASSAGES)}
        self.terms = {pid: Counter(words(row["text"])) for pid, row in self.passages.items()}
        self.lengths = {pid: sum(c.values()) for pid, c in self.terms.items()}
        self.average = sum(self.lengths.values()) / len(self.lengths)
        frequency: Counter[str] = Counter()
        for counts in self.terms.values():
            frequency.update(counts.keys())
        n = len(self.terms)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in frequency.items()}

    def search(self, query: str, service: str | None) -> list[dict]:
        scores = []
        for pid, counts in self.terms.items():
            if service and self.passages[pid]["domain"] != service:
                continue
            score = 0.0
            for term in set(words(query)):
                tf = counts.get(term, 0)
                if tf:
                    norm = tf + 1.2 * (1 - 0.75 + 0.75 * self.lengths[pid] / self.average)
                    score += self.idf[term] * tf * 2.2 / norm
            if score > 0:
                scores.append((-score, pid))
        found = []
        for _, pid in sorted(scores)[:5]:
            row = self.passages[pid]
            found.append({"passage": pid, "page": row["title"].split(" | ")[0], "text": row["text"]})
        return found


class Desk:
    """One task's desk: the caller's tickets and the advisers' free times, changed by the
    tools the agent calls."""

    def __init__(self, pages: Pages, state: dict) -> None:
        self.pages = pages
        self.state = copy.deepcopy(state)

    def call(self, name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments or "{}")
        except json.JSONDecodeError as error:
            return json.dumps({"error": f"The arguments aren't JSON: {error}"})
        try:
            result = getattr(self, "tool_" + name)(**args)
        except AttributeError:
            return json.dumps({"error": f"There is no tool named {name!r}."})
        except TypeError as error:
            return json.dumps({"error": str(error)})
        return json.dumps(result, ensure_ascii=False)

    def tool_search_help(self, query: str, service: str | None = None) -> dict:
        if service is not None and service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        return {"results": self.pages.search(query, service)}

    def tool_list_tickets(self) -> dict:
        return {"tickets": self.state["tickets"]}

    def tool_open_ticket(self, service: str, summary: str) -> dict:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        ticket = f"T-{3001 + len(self.state['opened'])}"
        self.state["tickets"].append({"ticket": ticket, "service": service, "status": "open", "summary": summary})
        self.state["opened"].append({"ticket": ticket, "service": service, "summary": summary})
        return {"ticket": ticket}

    def tool_free_callbacks(self, service: str, day: str) -> dict:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        if day not in DAYS:
            return {"error": "Advisers call back from 2026-11-02 to 2026-11-06."}
        return {"free": self.state["free"][service][day]}

    def tool_book_callback(self, ticket: str, day: str, time: str) -> dict:
        found = [t for t in self.state["tickets"] if t["ticket"] == ticket]
        if not found:
            return {"error": f"The caller has no ticket {ticket}."}
        if found[0]["status"] != "open":
            return {"error": f"Ticket {ticket} is closed."}
        service = found[0]["service"]
        if day not in DAYS or time not in self.state["free"][service].get(day, []):
            return {"error": f"{service}'s advisers aren't free on {day} at {time}."}
        self.state["free"][service][day].remove(time)
        self.state["booked"].append({"ticket": ticket, "day": day, "time": time})
        return {"booked": {"ticket": ticket, "day": day, "time": time}}


def free_times(rng_seed: int) -> dict:
    import random

    rng = random.Random(rng_seed)
    return {
        s: {d: sorted(rng.sample(TIMES, 4)) for d in DAYS} for s in SERVICES
    }


def tasks() -> list[dict]:
    """40 tasks: 10 questions from the help desk's test set, 10 cases for a person, 10
    callbacks about the caller's one open ticket, and 10 callbacks that could be about either of
    two open tickets."""
    import random

    rng = random.Random(7)
    questions = read(EVALS / "questions.csv")
    relevant: dict[str, list[str]] = {}
    for row in read(EVALS / "relevant.csv"):
        relevant.setdefault(row["question"], []).append(row["passage"])
    services = list(SERVICES)
    out = []
    chosen = []
    for service in services:
        chosen += [q for q in questions if q["domain"] == service][:3]
    for q in chosen[:10]:
        out.append({"kind": "question", "messages": [q["text"]], "tickets": [], "expect": {"cites": relevant[q["question"]], "service": q["domain"]}})
    for i in range(10):
        service = services[i % 4]
        text = CASES[service][(i // 4) % 3]
        out.append({"kind": "case", "messages": [text], "tickets": [], "expect": {"service": service}})
    for i in range(10):
        service = services[i % 4]
        other = services[(i + 1) % 4]
        topic = TOPICS[service][i % 3]
        day = rng.randrange(5)
        part = rng.choice(["morning", "afternoon"])
        tickets = [
            {"ticket": f"T-{2100 + i}", "service": service, "status": "open", "summary": topic[0].upper() + topic[1:]},
            {"ticket": f"T-{1900 + i}", "service": other, "status": "closed", "summary": TOPICS[other][0].capitalize()},
        ]
        text = f"Can someone call me back about my {topic} on {WEEKDAYS[day]} {part}?"
        out.append({"kind": "callback", "messages": [text], "tickets": tickets, "expect": {"ticket": f"T-{2100 + i}", "day": DAYS[day], "part": part}})
    for i in range(10):
        a, b = services[i % 4], services[(i + 2) % 4]
        day = rng.randrange(5)
        tickets = [
            {"ticket": f"T-{2200 + i}", "service": a, "status": "open", "summary": TOPICS[a][i % 3].capitalize()},
            {"ticket": f"T-{2300 + i}", "service": b, "status": "open", "summary": TOPICS[b][(i + 1) % 3].capitalize()},
        ]
        text = f"Can an adviser call me back on {WEEKDAYS[day]} morning?"
        out.append({"kind": "unclear", "messages": [text], "tickets": tickets, "expect": {}})
    for n, task in enumerate(out, start=1):
        task["task"] = f"t{n}"
        task["caller"] = NAMES[n % len(NAMES)]
        task["state"] = {"tickets": task.pop("tickets"), "free": free_times(n), "opened": [], "booked": []}
        if task["kind"] == "callback":
            expect = task["expect"]
            service = task["state"]["tickets"][0]["service"]
            free = task["state"]["free"][service][expect["day"]]
            if not any((t < "12:00") == (expect["part"] == "morning") for t in free):
                free.append("10:00" if expect["part"] == "morning" else "14:00")
                free.sort()
    return out


def grade(task: dict, state: dict, reply: str) -> dict:
    """Whether the agent did the task: the desk's state at the end, and its last reply."""
    kind, expect = task["kind"], task["expect"]
    opened, booked = state["opened"], state["booked"]
    if kind == "question":
        cited = set(re.findall(r"\[(p\d+)\]", reply))
        ok = not opened and not booked and bool(cited & set(expect["cites"]))
        return {"ok": ok, "cited": sorted(cited), "writes": len(opened) + len(booked)}
    if kind == "case":
        ok = len(opened) == 1 and opened[0]["service"] == expect["service"] and not booked
        return {"ok": ok, "opened": opened, "booked": booked}
    if kind == "callback":
        good = (
            len(booked) == 1
            and not opened
            and booked[0]["ticket"] == expect["ticket"]
            and booked[0]["day"] == expect["day"]
            and (booked[0]["time"] < "12:00") == (expect["part"] == "morning")
        )
        ok = good and booked[0]["time"] in reply
        return {"ok": ok, "opened": opened, "booked": booked}
    ok = not opened and not booked and "?" in reply
    return {"ok": ok, "opened": opened, "booked": booked}
