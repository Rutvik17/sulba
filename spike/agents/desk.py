"""Spike 2: the help desk's desk for an agent trial. Its help pages are searched as Retrieval's
fused search does: BM25 and nomic-embed-text-v1.5's vectors by reciprocal rank fusion, each text
once. Each task has its own tickets and free callback times; it's
graded in code from the desk's writes, the turn each came in, and the agent's last reply."""

import copy
import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL = ROOT / "courses/ai-engineering/modules/retrieval/labs/hybrid-search-and-reranking/data"
EVALS = ROOT / "courses/ai-engineering/modules/evals/labs/test-sets/data"

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

SYSTEM = (
    "You are the assistant of a help desk for four US public services: Social Security (ssa), "
    "veterans' benefits (va), federal student aid (studentaid) and New York State's DMV (dmv). "
    "The caller is signed in, and the tools act on their account. Today is Friday 30 October "
    "2026. Advisers call back on Monday 2026-11-02, Tuesday 2026-11-03, Wednesday 2026-11-04, "
    "Thursday 2026-11-05 and Friday 2026-11-06, on the hour from 09:00 to 16:00; morning is "
    "before 12:00.\n\n"
    "- Answer questions about the services from their help pages: search them, and cite each "
    "passage you use by its id in square brackets, like [p17]. If the pages don't answer, say "
    "so.\n"
    "- A question about the caller's own case needs a person: offer to open a ticket for its "
    "service.\n"
    "- A callback is booked for one of the caller's open tickets, at a time its service's "
    "advisers are free.\n"
    "- Before you open a ticket or book a callback, tell the caller exactly what you'll do and "
    "ask them to confirm. Do it only once they say yes.\n"
    "- If you can't tell what the caller wants, ask them."
)

DAY = {
    "type": "string",
    "enum": list(DAYS),
    "description": "Monday 2026-11-02 to Friday 2026-11-06.",
}
SERVICE = {"type": "string", "enum": list(SERVICES)}
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
                    "service": {**SERVICE, "description": "Search only this service's pages."},
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
            "description": "Open a ticket for an adviser to look into the caller's case. Gives "
            "the new ticket's id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": SERVICE,
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
                "properties": {"service": SERVICE, "day": DAY},
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
                    "day": DAY,
                    "time": {"type": "string", "enum": TIMES},
                },
                "required": ["ticket", "day", "time"],
            },
        },
    },
]

TOPICS = {
    "ssa": ["replacement Social Security card", "disability benefits application", "retirement benefits start date", "Medicare enrollment"],
    "va": ["GI Bill payment", "disability compensation claim", "VA health care enrollment", "pension application"],
    "studentaid": ["FAFSA correction", "student loan repayment plan", "Pell Grant", "loan forgiveness application"],
    "dmv": ["road test appointment", "driver license renewal", "suspended registration", "vehicle title transfer"],
}
CASES = {
    "ssa": [
        "I applied for disability benefits six weeks ago and haven't heard anything. Can someone check on my application?",
        "My Social Security payment this month was smaller than usual and nobody told me why.",
        "I reported my new address in September but my letters still go to the old one.",
        "I got a letter saying I was overpaid and have to pay money back, but I don't think that's right.",
    ],
    "va": [
        "My GI Bill housing payment for October never arrived. Can someone look at my account?",
        "I sent more evidence for my disability claim a month ago and the status hasn't changed.",
        "I was told my VA health care enrollment went through but I never got an appointment letter.",
        "My pension stopped after I moved and I don't know why. Can a person look into it?",
    ],
    "studentaid": [
        "My loan servicer says my repayment plan changed but I never asked for that.",
        "I submitted a correction to my FAFSA two weeks ago and my school still sees the old one.",
        "My Pell Grant didn't show up on my school bill this term. What happened?",
        "I was approved for forgiveness in the summer but my loan balance is still there.",
    ],
    "dmv": [
        "I paid my tolls but my registration still shows as suspended. Can someone look at my record?",
        "I renewed my license online three weeks ago and the new card hasn't come.",
        "My road test appointment disappeared from my account.",
        "I sold my car last month but the DMV still has it in my name.",
    ],
}
ASKS = [
    "Can someone call me back about my {topic} on {weekday} {part}?",
    "I'd like an adviser to phone me {weekday} {part} about my {topic}.",
    "Could I get a call {weekday} {part}? It's about my {topic}.",
    "Please have someone ring me on {weekday} {part} about the {topic}.",
]
NEW = [
    "I need to talk to someone about my {topic}. Can they call me {weekday} {part}? There's no ticket for it yet.",
    "Can an adviser call me {weekday} {part} about my {topic}? I haven't opened a ticket about it.",
    "I'd like a call {weekday} {part} about my {topic}. This is the first time I'm asking about it.",
]
VAGUE = [
    "Can an adviser call me back on {weekday} {part}?",
    "I'd like a callback {weekday} {part}, please.",
    "Could someone ring me {weekday} {part}?",
]
YES = "Yes, please go ahead."


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def passages() -> dict[str, dict[str, str]]:
    return {row["passage"]: row for row in read(RETRIEVAL / "passages.csv")}


class Desk:
    """One task's desk: the caller's tickets and the advisers' free times, changed by the tools
    the agent calls, with each write's turn."""

    def __init__(self, search, state: dict) -> None:
        self.search = search
        self.state = copy.deepcopy(state)
        self.turn = 0
        self.searches: list[dict] = []

    def call(self, name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments or "{}")
            if not isinstance(args, dict):
                raise ValueError("not an object")
        except (json.JSONDecodeError, ValueError) as error:
            return json.dumps({"error": f"The arguments aren't a JSON object: {error}"})
        method = getattr(self, "tool_" + name, None)
        if method is None:
            return json.dumps({"error": f"There is no tool named {name!r}."})
        try:
            result = method(**args)
        except TypeError as error:
            return json.dumps({"error": str(error)})
        return json.dumps(result, ensure_ascii=False)

    def tool_search_help(self, query: str, service: str | None = None) -> dict:
        if service is not None and service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        found, seconds = self.search(query, service)
        self.searches.append({"query": query, "service": service, "found": [f["passage"] for f in found], "seconds": seconds})
        return {"results": found}

    def tool_list_tickets(self) -> dict:
        return {"tickets": self.state["tickets"]}

    def tool_open_ticket(self, service: str, summary: str) -> dict:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        ticket = f"T-{3001 + len(self.state['opened'])}"
        self.state["tickets"].append({"ticket": ticket, "service": service, "status": "open", "summary": summary})
        self.state["opened"].append({"ticket": ticket, "service": service, "summary": summary, "turn": self.turn})
        return {"ticket": ticket}

    def tool_free_callbacks(self, service: str, day: str) -> dict:
        if service not in SERVICES:
            return {"error": f"service is one of {', '.join(SERVICES)}."}
        if day not in DAYS:
            return {"error": "day is one of 2026-11-02 to 2026-11-06."}
        return {"day": day, "free": self.state["free"][service][day]}

    def tool_book_callback(self, ticket: str, day: str, time: str) -> dict:
        found = [t for t in self.state["tickets"] if t["ticket"] == ticket]
        if not found:
            return {"error": f"The caller has no ticket {ticket}."}
        if found[0]["status"] != "open":
            return {"error": f"Ticket {ticket} is closed."}
        service = found[0]["service"]
        if day not in DAYS or time not in self.state["free"][service].get(day, []):
            return {"error": f"The {service} advisers aren't free on {day} at {time}."}
        self.state["free"][service][day].remove(time)
        self.state["booked"].append({"ticket": ticket, "day": day, "time": time, "turn": self.turn})
        return {"booked": {"ticket": ticket, "day": day, "time": time}}


def free_times(rng: random.Random) -> dict:
    return {s: {d: sorted(rng.sample(TIMES, 4)) for d in DAYS} for s in SERVICES}


def ensure_free(state: dict, service: str, day: str, part: str) -> None:
    free = state["free"][service][day]
    if not any((t < "12:00") == (part == "morning") for t in free):
        free.append("10:00" if part == "morning" else "14:00")
        free.sort()


def tasks() -> list[dict]:
    """96 tasks: 40 questions from the help desk's test set, 10 a service; 16 cases for a
    person; 16 callbacks about the caller's open ticket; 12 callbacks about something with no
    ticket yet; and 12 callbacks that could be about either of two open tickets."""
    rng = random.Random(7)
    questions = read(EVALS / "questions.csv")
    relevant: dict[str, list[str]] = {}
    for row in read(EVALS / "relevant.csv"):
        relevant.setdefault(row["question"], []).append(row["passage"])
    services = list(SERVICES)
    days = list(DAYS)
    out = []
    for service in services:
        mine = [q for q in questions if q["domain"] == service]
        for q in rng.sample(mine, 10):
            out.append({"kind": "question", "messages": [q["text"]], "tickets": [], "expect": {"cites": relevant[q["question"]], "service": service, "question": q["question"]}})
    for i in range(16):
        service = services[i % 4]
        out.append({"kind": "case", "messages": [CASES[service][i // 4], YES], "tickets": [], "expect": {"service": service}})
    for i in range(16):
        service, other = services[i % 4], services[(i + 1) % 4]
        topic = TOPICS[service][i // 4]
        day, part = rng.choice(days), rng.choice(["morning", "afternoon"])
        tickets = [
            {"ticket": f"T-{2100 + i}", "service": service, "status": "open", "summary": topic[0].upper() + topic[1:]},
            {"ticket": f"T-{1900 + i}", "service": other, "status": "closed", "summary": TOPICS[other][i // 4][0].upper() + TOPICS[other][i // 4][1:]},
        ]
        text = ASKS[i % 4].format(topic=topic, weekday=DAYS[day], part=part)
        out.append({"kind": "callback", "messages": [text, YES], "tickets": tickets, "expect": {"ticket": f"T-{2100 + i}", "service": service, "day": day, "part": part}})
    for i in range(12):
        service, other = services[i % 4], services[(i + 2) % 4]
        topic = TOPICS[service][(i // 4 + 1) % 4]
        day, part = rng.choice(days), rng.choice(["morning", "afternoon"])
        tickets = [{"ticket": f"T-{2400 + i}", "service": other, "status": "open", "summary": TOPICS[other][i // 4].capitalize()}]
        text = NEW[i % 3].format(topic=topic, weekday=DAYS[day], part=part)
        out.append({"kind": "new", "messages": [text, YES], "tickets": tickets, "expect": {"service": service, "day": day, "part": part}})
    for i in range(12):
        a, b = services[i % 4], services[(i + 2) % 4]
        day, part = rng.choice(days), rng.choice(["morning", "afternoon"])
        tickets = [
            {"ticket": f"T-{2200 + i}", "service": a, "status": "open", "summary": TOPICS[a][i // 4].capitalize()},
            {"ticket": f"T-{2300 + i}", "service": b, "status": "open", "summary": TOPICS[b][(i // 4 + 1) % 4].capitalize()},
        ]
        text = VAGUE[i % 3].format(weekday=DAYS[day], part=part)
        out.append({"kind": "unclear", "messages": [text, YES], "tickets": tickets, "expect": {}})
    for n, task in enumerate(out, start=1):
        task["task"] = f"t{n}"
        task["state"] = {"tickets": task.pop("tickets"), "free": free_times(rng), "opened": [], "booked": []}
        e = task["expect"]
        if task["kind"] in ("callback", "new"):
            ensure_free(task["state"], e["service"], e["day"], e["part"])
    return out


TIME = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?", re.IGNORECASE)


def times_in(reply: str) -> set[str]:
    """Every time of day the reply names, as HH:MM."""
    found = set()
    for hour, minute, half in TIME.findall(reply):
        h = int(hour)
        if half.lower().startswith("p") and h < 12:
            h += 12
        if (minute or half) and 0 <= h < 24:
            found.add(f"{h:02d}:{minute or '00'}")
    return found


def grade(task: dict, state: dict, reply: str, last_turn: int) -> dict:
    """Whether the agent did the task, from the desk's writes, the turn of each, and its last
    reply. A write before the caller's yes is a write without confirmation."""
    kind, e = task["kind"], task["expect"]
    opened, booked = state["opened"], state["booked"]
    early = any(w["turn"] < len(task["messages"]) - 1 for w in opened + booked)
    out = {"early": early, "writes": len(opened) + len(booked)}
    if kind == "question":
        cited = set(re.findall(r"\[(p\d+)\]", reply))
        out |= {"ok": not opened and not booked and bool(cited & set(e["cites"])), "cited": sorted(cited)}
    elif kind == "case":
        out["ok"] = len(opened) == 1 and opened[0]["service"] == e["service"] and not booked and not early
    elif kind == "callback":
        b = booked[0] if len(booked) == 1 else None
        right = b is not None and b["ticket"] == e["ticket"] and b["day"] == e["day"] and (b["time"] < "12:00") == (e["part"] == "morning")
        out["ok"] = right and not opened and not early and b["time"] in times_in(reply)
    elif kind == "new":
        b = booked[0] if len(booked) == 1 else None
        right = (
            len(opened) == 1 and opened[0]["service"] == e["service"] and b is not None
            and b["ticket"] == opened[0]["ticket"] and b["day"] == e["day"]
            and (b["time"] < "12:00") == (e["part"] == "morning")
        )
        out["ok"] = right and not early and b["time"] in times_in(reply)
    else:
        out["ok"] = not opened and not booked
    out["ended_turn"] = last_turn
    return out
