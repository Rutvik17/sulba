"""Granite Guardian's verdict on whether a reply keeps to its passages."""

from pathlib import Path

import httpx
import jinja2

# How many of the likeliest first tokens the server gives, as IBM's model card reads them.
LIKELIEST = 20


def template(path: Path) -> jinja2.Template:
    """The chat template in a tokenizer's configuration, compiled as transformers compiles
    one."""
    raise NotImplementedError


def prompt(chat: jinja2.Template, context: str, reply: str, today: str) -> str:
    """The prompt that asks whether the reply says anything its context doesn't, with the
    date the template writes as today's."""
    raise NotImplementedError


def risk(client: httpx.Client, text: str) -> float:
    """The probability the grader gives "Yes", that the reply says something its context
    doesn't, over its probability of "Yes" or "No"."""
    raise NotImplementedError
