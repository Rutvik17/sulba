# /// script
# requires-python = "==3.14.2"
# ///
"""Writes the help desk's tasks for the Agents labs, `tasks.json`: scripted conversations with
the desk, each with the caller's messages, the help pages the chat was opened from, the caller's
tickets, the advisers' free callback times, and what the desk must do.

The desk answers questions about four US public services from their help pages, and does its own
work: it looks up the caller's tickets, opens a ticket for an adviser and books an adviser to
call back about a ticket, from Monday 2 to Friday 6 November 2026, on the hour from 09:00 to
16:00. Each service's advisers have four of those eight times free each day, drawn at random.

The 120 tasks, 30 of each service but the vague ones:

- 40 questions, 10 of each service, drawn at random from the help desk's questions of seven
  words or more, with the passages that hold each one's answer, as `multidoc2dial_evals.py`
  builds them; a shorter one, such as "Will they be continued?", leaves out what it's about.
  The chat was opened from the question's service's pages, and the desk must cite a passage
  that holds the answer and change nothing.
- 20 cases, 5 of each service, about the caller's own case, which only an adviser can look
  into. The desk must open one ticket for the service, once the caller says yes.
- 20 callbacks, 5 of each service, about the caller's one open ticket for the service, at a time
  that is free or at any free time in a morning or an afternoon. The desk must book that ticket
  at that time, once the caller says yes, and say the time it booked.
- 20 new callbacks, 5 of each service, about something with no ticket yet, in a morning or an
  afternoon. The desk must open a ticket for the service and book it, once the caller says yes,
  and say the time.
- 20 vague callbacks, opened from the help desk's home page by a caller with open tickets for two
  services, which don't say which ticket they're about. The desk must change nothing.

Python's random.Random with seed 7 draws the questions, the days, the times and the free times,
in that order.

    uv run tools/datasets/agents_tasks.py <folder with questions.csv and relevant.csv> <out>
"""

import csv
import json
import random
import sys
from pathlib import Path

SERVICES = ["ssa", "va", "studentaid", "dmv"]
# The fewest words a question may have.
WORDS = 7
DAYS = {
    "2026-11-02": "Monday",
    "2026-11-03": "Tuesday",
    "2026-11-04": "Wednesday",
    "2026-11-05": "Thursday",
    "2026-11-06": "Friday",
}
TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
# What a caller's tickets are about, five for each service.
TOPICS = {
    "ssa": [
        "replacement Social Security card",
        "disability benefits application",
        "retirement benefits start date",
        "survivors benefits claim",
        "Medicare enrollment",
    ],
    "va": [
        "GI Bill housing payment",
        "disability compensation claim",
        "VA health care enrollment",
        "pension application",
        "decision review request",
    ],
    "studentaid": [
        "FAFSA correction",
        "student loan repayment plan",
        "Pell Grant award",
        "loan forgiveness application",
        "loan deferment request",
    ],
    "dmv": [
        "road test appointment",
        "driver license renewal",
        "suspended registration",
        "vehicle title transfer",
        "change of address",
    ],
}
# The cases, five for each service: problems with the caller's own case.
CASES = {
    "ssa": [
        "I applied for disability benefits six weeks ago and haven't heard anything. Can "
        "someone check on my application?",
        "My Social Security payment this month was smaller than usual and nobody told me why.",
        "I reported my new address in September but my letters still go to the old one.",
        "I got a letter saying I was overpaid and have to pay money back, but I don't think "
        "that's right.",
        "My replacement card was supposed to arrive two weeks ago and it still hasn't come.",
    ],
    "va": [
        "My GI Bill housing payment for October never arrived. Can someone look at my account?",
        "I sent more evidence for my disability claim a month ago and the status hasn't changed.",
        "I was told my VA health care enrollment went through but I never got an appointment "
        "letter.",
        "My pension stopped after I moved and I don't know why.",
        "My decision review says it's closed but I never got a decision letter.",
    ],
    "studentaid": [
        "My loan servicer says my repayment plan changed but I never asked for that.",
        "I submitted a correction to my FAFSA two weeks ago and my school still sees the old one.",
        "My Pell Grant didn't show up on my school bill this term.",
        "I was approved for forgiveness in the summer but my loan balance is still there.",
        "My deferment was approved but my servicer still says I have a payment due.",
    ],
    "dmv": [
        "I paid my tolls but my registration still shows as suspended.",
        "I renewed my license online three weeks ago and the new card hasn't come.",
        "My road test appointment disappeared from my account.",
        "I sold my car last month but it's still in my name.",
        "I changed my address online but my renewal notice went to my old address.",
    ],
}
OPEN_CASE = "Yes, please open the ticket."
AT = [
    "Can someone call me back about my {topic} on {weekday} at {time}?",
    "I'd like an adviser to phone me on {weekday} at {time} about my {topic}.",
]
DURING = [
    "Could I get a call on {weekday} {part}? It's about my {topic}.",
    "Please have someone ring me {weekday} {part} about the {topic}.",
]
BOOK_AT = "Yes, please book it."
BOOK_DURING = "Yes, please go ahead. Any time that {part} is fine."
NEW = [
    "I need to talk to someone about my {topic}. Can they call me {weekday} {part}? There's no "
    "ticket for it yet.",
    "Can an adviser call me {weekday} {part} about my {topic}? I haven't opened a ticket about it.",
]
BOOK_NEW = "Yes, please open it and book the call. Any time that {part} is fine."
VAGUE = [
    "Can an adviser call me back on {weekday} {part}?",
    "I'd like a callback {weekday} {part}, please.",
    "Could someone ring me {weekday} {part}?",
    "Can I get a call from an adviser on {weekday} {part}?",
]
YES = "Yes, please."


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def capital(text: str) -> str:
    return text[0].upper() + text[1:]


def morning(time: str) -> bool:
    return time < "12:00"


def tasks(folder: Path) -> list[dict]:
    rng = random.Random(7)
    questions = read(folder / "questions.csv")
    relevant: dict[str, list[str]] = {}
    for row in read(folder / "relevant.csv"):
        relevant.setdefault(row["question"], []).append(row["passage"])
    out: list[dict] = []
    for service in SERVICES:
        mine = [
            question
            for question in questions
            if question["domain"] == service and len(question["text"].split()) >= WORDS
        ]
        for question in rng.sample(mine, 10):
            out.append(
                {
                    "kind": "question",
                    "page": service,
                    "messages": [question["text"]],
                    "tickets": [],
                    "expect": {"cites": relevant[question["question"]]},
                }
            )
    for service in SERVICES:
        for text in CASES[service]:
            out.append(
                {
                    "kind": "case",
                    "page": service,
                    "messages": [text, OPEN_CASE],
                    "tickets": [],
                    "expect": {"service": service},
                }
            )
    days = list(DAYS)
    for i in range(20):
        service, other = SERVICES[i % 4], SERVICES[(i + 1) % 4]
        topic = TOPICS[service][i // 4]
        day = rng.choice(days)
        tickets = [
            {
                "ticket": f"T-{2101 + i}",
                "service": service,
                "status": "open",
                "summary": capital(topic),
            },
            {
                "ticket": f"T-{1901 + i}",
                "service": other,
                "status": "closed",
                "summary": capital(TOPICS[other][i // 4]),
            },
        ]
        if i % 2 == 0:
            time = rng.choice(TIMES)
            text = AT[(i // 2) % 2].format(topic=topic, weekday=DAYS[day], time=time)
            messages, expect = [text, BOOK_AT], {"time": time}
        else:
            part = rng.choice(["morning", "afternoon"])
            text = DURING[(i // 2) % 2].format(topic=topic, weekday=DAYS[day], part=part)
            messages, expect = [text, BOOK_DURING.format(part=part)], {"part": part}
        out.append(
            {
                "kind": "callback",
                "page": service,
                "messages": messages,
                "tickets": tickets,
                "expect": {"ticket": f"T-{2101 + i}", "day": day, **expect},
            }
        )
    for i in range(20):
        service, other = SERVICES[i % 4], SERVICES[(i + 2) % 4]
        topic = TOPICS[service][(i // 4 + 2) % 5]
        day, part = rng.choice(days), rng.choice(["morning", "afternoon"])
        tickets = [
            {
                "ticket": f"T-{2201 + i}",
                "service": other,
                "status": "open",
                "summary": capital(TOPICS[other][i // 4]),
            }
        ]
        text = NEW[i % 2].format(topic=topic, weekday=DAYS[day], part=part)
        out.append(
            {
                "kind": "new",
                "page": service,
                "messages": [text, BOOK_NEW.format(part=part)],
                "tickets": tickets,
                "expect": {"service": service, "day": day, "part": part},
            }
        )
    for i in range(20):
        a, b = SERVICES[i % 4], SERVICES[(i + 1 + (i // 4) % 3) % 4]
        day, part = rng.choice(days), rng.choice(["morning", "afternoon"])
        tickets = [
            {
                "ticket": f"T-{2301 + i}",
                "service": a,
                "status": "open",
                "summary": capital(TOPICS[a][i // 4]),
            },
            {
                "ticket": f"T-{2401 + i}",
                "service": b,
                "status": "open",
                "summary": capital(TOPICS[b][(i // 4 + 1) % 5]),
            },
        ]
        text = VAGUE[i % 4].format(weekday=DAYS[day], part=part)
        out.append(
            {
                "kind": "vague",
                "page": None,
                "messages": [text, YES],
                "tickets": tickets,
                "expect": {},
            }
        )
    for number, task in enumerate(out, start=1):
        task["task"] = f"t{number}"
        free = {
            service: {day: sorted(rng.sample(TIMES, 4)) for day in DAYS} for service in SERVICES
        }
        expect = task["expect"]
        if task["kind"] == "callback":
            service = task["tickets"][0]["service"]
            times = free[service][expect["day"]]
            if "time" in expect and expect["time"] not in times:
                times[rng.randrange(4)] = expect["time"]
                times.sort()
            if "part" in expect and not any(
                morning(t) == (expect["part"] == "morning") for t in times
            ):
                times[rng.randrange(4)] = rng.choice(
                    [t for t in TIMES if morning(t) == (expect["part"] == "morning")]
                )
                times.sort()
        if task["kind"] == "new":
            times = free[expect["service"]][expect["day"]]
            if not any(morning(t) == (expect["part"] == "morning") for t in times):
                times[rng.randrange(4)] = rng.choice(
                    [t for t in TIMES if morning(t) == (expect["part"] == "morning")]
                )
                times.sort()
        task["free"] = free
    return [
        {
            key: task[key]
            for key in ("task", "kind", "page", "messages", "tickets", "free", "expect")
        }
        for task in out
    ]


if __name__ == "__main__":
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        json.dump(tasks(folder), file, ensure_ascii=False, indent=1)
        file.write("\n")
