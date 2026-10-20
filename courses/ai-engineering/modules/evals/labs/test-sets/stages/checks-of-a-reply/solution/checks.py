"""Checks of the help desk's replies, written in code."""

import re

CITED = re.compile(r"\[(p\d+)\]")

Checks = dict[str, bool]


def cited(reply: str) -> list[str]:
    """The passages a reply cites by name, each once, in the order it first cites them."""
    return list(dict.fromkeys(CITED.findall(reply)))


def checks(
    reply: str, finish: str, shown: list[str], relevant: set[str], most: int
) -> Checks:
    """Whether the reply passes each check: it cites a passage, cites only passages it was
    shown, cites one that holds the answer, ended by itself, and keeps to `most` words."""
    names = cited(reply)
    return {
        "cites": bool(names),
        "cites_shown": all(name in shown for name in names),
        "cites_answer": any(name in relevant for name in names),
        "finished": finish == "stop",
        "brief": len(reply.split()) <= most,
    }


def pass_rates(results: list[Checks]) -> dict[str, float]:
    """Each check's share of the replies that pass it, and `all`, the share that pass every
    check."""
    rates = {
        name: sum(result[name] for result in results) / len(results)
        for name in results[0]
    }
    rates["all"] = sum(all(result.values()) for result in results) / len(results)
    return rates
