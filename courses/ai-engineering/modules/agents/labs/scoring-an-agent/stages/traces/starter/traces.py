"""Traces of an agent's runs in OpenTelemetry's conventions for generative AI: a span for the
agent, one for each chat request and one for each tool it runs; and from the spans, each run's
row as runs.csv has it."""

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import httpx
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

PROVIDER = "llama.cpp"


class Traced:
    """An httpx.Client whose chat requests each have a span: what the request asked for, and
    what came back or the error it ended in."""

    def __init__(self, client: httpx.Client, tracer: Tracer) -> None:
        self.client = client
        self.tracer = tracer

    def post(self, url: str, *, json: dict[str, Any]) -> httpx.Response:
        """The client's response to a chat request, traced."""
        raise NotImplementedError


def tool(tracer: Tracer, call: Callable[[str, str], str]) -> Callable[[str, str], str]:
    """call, which runs a tool by its name with its arguments as JSON text, with a span for
    each tool it runs."""
    raise NotImplementedError


@contextmanager
def agent(tracer: Tracer, name: str, model: str) -> Iterator[Span]:
    """A span for one run of the agent called name, on model, current while it lasts."""
    raise NotImplementedError
    yield


def runs(spans: Sequence[ReadableSpan]) -> list[dict[str, str]]:
    """A row for each run, a trace whose first span is an agent's, in the order the runs
    began: its seconds, its chat requests and their tokens of prompt and of reply, the tools it
    ran, and the error it ended in, or "" if none."""
    raise NotImplementedError
