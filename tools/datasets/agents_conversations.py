# /// script
# requires-python = "==3.14.2"
# ///
"""Writes the help desk's long conversations for the Memory and sub-agents lab,
`conversations.json`: scripted conversations of 15 messages with the desk, each with the help
pages the chat was opened from, the caller's tickets, the advisers' free callback times, and its
parts, each with the caller's messages and what the desk must do.

The 16 conversations, 4 opened from each service's pages, each in this order:

- the caller says the part of the day, morning or afternoon, when they can take a call;
- 5 questions about the service, drawn at random from the help desk's questions of seven words
  or more, with the passages that hold each one's answer, as `multidoc2dial_evals.py` builds
  them, no question in two conversations. The desk must cite a passage that holds the answer
  and change nothing;
- a callback about the caller's open ticket for the service, on a weekday, which doesn't say the
  part of the day, then the caller's yes. The desk must book the ticket on that day, in the part
  of the day the caller first said, once the caller says yes, and say the time it booked;
- 5 more questions, as before;
- a callback about the caller's open ticket for another service, on another weekday, then the
  caller's yes, as before.

The callbacks come from Monday 2 to Friday 6 November 2026, on the hour from 09:00 to 16:00.
Each service's advisers have four of those eight times free each day, at least one of them in
each part of the day, drawn at random.

Python's random.Random with seed 7 draws the questions, the parts of the day, the days and the
free times, in that order.

    uv run tools/datasets/agents_conversations.py \\
        <folder with questions.csv and relevant.csv> <out>
"""

import csv
import json
import random
import sys
from pathlib import Path

SERVICES = ["ssa", "va", "studentaid", "dmv"]
# The conversations opened from each service's pages, and the questions in each half of one.
CONVERSATIONS = 4
QUESTIONS = 5
WORDS = 7
DAYS = {
    "2026-11-02": "Monday",
    "2026-11-03": "Tuesday",
    "2026-11-04": "Wednesday",
    "2026-11-05": "Thursday",
    "2026-11-06": "Friday",
}
TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
# What a caller's open tickets are about, four for each service.
TOPICS = {
    "ssa": [
        "replacement Social Security card",
        "disability benefits application",
        "retirement benefits start date",
        "Medicare enrollment",
    ],
    "va": [
        "disability compensation claim",
        "GI Bill benefits",
        "VA home loan certificate",
        "pension application",
    ],
    "studentaid": [
        "FAFSA correction",
        "loan repayment plan",
        "Pell Grant eligibility",
        "loan forgiveness application",
    ],
    "dmv": [
        "driver license renewal",
        "vehicle registration",
        "learner permit test",
        "license plate replacement",
    ],
}
PARTS = [
    "Hello. Before anything else: I can only take calls in the {part}.",
    "Hi. Just so you know, I'm only free to talk on the phone in the {part}.",
]
CALLBACKS = [
    "Could an adviser call me on {weekday} about my {topic}?",
    "I'd like a call back about my {topic} on {weekday}, please.",
]
YES = "Yes, please."


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def capital(text: str) -> str:
    return text[0].upper() + text[1:]


def free_times(rng: random.Random) -> dict[str, list[str]]:
    """Four of each day's eight times, at least one before noon and one after."""
    free = {}
    for day in DAYS:
        while True:
            times = sorted(rng.sample(TIMES, 4))
            if any(time < "12:00" for time in times) and any(time >= "12:00" for time in times):
                break
        free[day] = times
    return free


def conversations(folder: Path) -> list[dict]:
    rng = random.Random(7)
    questions = read(folder / "questions.csv")
    relevant: dict[str, list[str]] = {}
    for row in read(folder / "relevant.csv"):
        relevant.setdefault(row["question"], []).append(row["passage"])
    drawn = {}
    for service in SERVICES:
        mine = [
            question
            for question in questions
            if question["domain"] == service and len(question["text"].split()) >= WORDS
        ]
        drawn[service] = rng.sample(mine, CONVERSATIONS * 2 * QUESTIONS)
    parts = [rng.choice(["morning", "afternoon"]) for _ in range(len(SERVICES) * CONVERSATIONS)]
    out = []
    for i in range(len(SERVICES) * CONVERSATIONS):
        service, other = SERVICES[i % 4], SERVICES[(i + 1) % 4]
        n, part = i // 4, parts[i]
        first, second = rng.sample(list(DAYS), 2)
        tickets = [
            {
                "ticket": f"T-{3101 + i}",
                "service": service,
                "status": "open",
                "summary": capital(TOPICS[service][n]),
            },
            {
                "ticket": f"T-{3201 + i}",
                "service": other,
                "status": "open",
                "summary": capital(TOPICS[other][n]),
            },
        ]
        asked = drawn[service][n * 2 * QUESTIONS : (n + 1) * 2 * QUESTIONS]
        ask = [
            {
                "kind": "question",
                "messages": [question["text"]],
                "expect": {"cites": relevant[question["question"]]},
            }
            for question in asked
        ]
        callbacks = [
            {
                "kind": "callback",
                "messages": [
                    CALLBACKS[(i + j) % 2].format(
                        weekday=DAYS[day], topic=TOPICS[ticket["service"]][n]
                    ),
                    YES,
                ],
                "expect": {"ticket": ticket["ticket"], "day": day, "part": part},
            }
            for j, (ticket, day) in enumerate(zip(tickets, (first, second), strict=True))
        ]
        out.append(
            {
                "conversation": f"c{i + 1}",
                "page": service,
                "tickets": tickets,
                "free": {each: free_times(rng) for each in SERVICES},
                "parts": [
                    {
                        "kind": "preference",
                        "messages": [PARTS[i % 2].format(part=part)],
                        "expect": {},
                    },
                    *ask[:QUESTIONS],
                    callbacks[0],
                    *ask[QUESTIONS:],
                    callbacks[1],
                ],
            }
        )
    return out


if __name__ == "__main__":
    folder, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.write_text(
        json.dumps(conversations(folder), indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
