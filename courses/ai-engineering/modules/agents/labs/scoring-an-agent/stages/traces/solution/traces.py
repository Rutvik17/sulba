"""Traces of an agent's runs in OpenTelemetry's conventions for generative AI: a span for the
agent, one for each chat request and one for each tool it runs; and from the spans, each run's
row as runs.csv has it."""

from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import httpx
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer

PROVIDER = "llama.cpp"
# The request's settings and the attributes they go in.
SETTINGS = {
    "max_tokens": "gen_ai.request.max_tokens",
    "temperature": "gen_ai.request.temperature",
    "top_p": "gen_ai.request.top_p",
    "top_k": "gen_ai.request.top_k",
    "presence_penalty": "gen_ai.request.presence_penalty",
    "seed": "gen_ai.request.seed",
}
DEFAULT_PORTS = {"http": 80, "https": 443}


class Traced:
    """An httpx.Client whose chat requests each have a span: what the request asked for, and
    what came back or the error it ended in."""

    def __init__(self, client: httpx.Client, tracer: Tracer) -> None:
        self.client = client
        self.tracer = tracer

    def post(self, url: str, *, json: dict[str, Any]) -> httpx.Response:
        """The client's response to a chat request, traced."""
        model = json["model"]
        base = self.client.base_url
        attributes: dict[str, Any] = {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": PROVIDER,
            "gen_ai.request.model": model,
            "server.address": base.host,
            "server.port": base.port or DEFAULT_PORTS[base.scheme],
        }
        for setting, attribute in SETTINGS.items():
            if setting in json:
                attributes[attribute] = json[setting]
        with self.tracer.start_as_current_span(
            f"chat {model}", kind=SpanKind.CLIENT, attributes=attributes
        ) as span:
            try:
                response = self.client.post(url, json=json)
            except httpx.HTTPError as error:
                span.set_attribute("error.type", type(error).__qualname__)
                raise
            if response.is_error:
                span.set_attribute("error.type", str(response.status_code))
                span.set_status(Status(StatusCode.ERROR))
                return response
            answer = response.json()
            usage = answer.get("usage") or {}
            span.set_attributes(
                {
                    "gen_ai.response.id": answer["id"],
                    "gen_ai.response.model": answer["model"],
                    "gen_ai.response.finish_reasons": [
                        choice["finish_reason"] for choice in answer["choices"]
                    ],
                    "gen_ai.usage.input_tokens": usage.get("prompt_tokens", 0),
                    "gen_ai.usage.output_tokens": usage.get("completion_tokens", 0),
                }
            )
            return response


def tool(tracer: Tracer, call: Callable[[str, str], str]) -> Callable[[str, str], str]:
    """call, which runs a tool by its name with its arguments as JSON text, with a span for
    each tool it runs."""

    def traced(name: str, arguments: str) -> str:
        with tracer.start_as_current_span(
            f"execute_tool {name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": name,
                "gen_ai.tool.type": "function",
            },
        ) as span:
            try:
                return call(name, arguments)
            except Exception as error:
                span.set_attribute("error.type", type(error).__qualname__)
                raise

    return traced


@contextmanager
def agent(tracer: Tracer, name: str, model: str) -> Iterator[Span]:
    """A span for one run of the agent called name, on model, current while it lasts."""
    with tracer.start_as_current_span(
        f"invoke_agent {name}",
        kind=SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.provider.name": PROVIDER,
            "gen_ai.agent.name": name,
            "gen_ai.request.model": model,
        },
    ) as span:
        try:
            yield span
        except Exception as error:
            span.set_attribute("error.type", type(error).__qualname__)
            raise


def runs(spans: Sequence[ReadableSpan]) -> list[dict[str, str]]:
    """A row for each run, a trace whose first span is an agent's, in the order the runs
    began: its seconds, its chat requests and their tokens of prompt and of reply, the tools it
    ran, and the error it ended in, or "" if none."""
    traces: dict[int, list[ReadableSpan]] = defaultdict(list)
    for span in spans:
        traces[span.context.trace_id].append(span)
    found = []
    for trace in traces.values():
        root = next((span for span in trace if span.parent is None), None)
        if root is not None and operation(root) == "invoke_agent":
            found.append((root, trace))
    found.sort(key=lambda each: each[0].start_time or 0)
    return [row(root, trace) for root, trace in found]


def operation(span: ReadableSpan) -> object:
    return (span.attributes or {}).get("gen_ai.operation.name")


def row(root: ReadableSpan, trace: list[ReadableSpan]) -> dict[str, str]:
    chats = [span.attributes or {} for span in trace if operation(span) == "chat"]
    seconds = ((root.end_time or 0) - (root.start_time or 0)) / 1e9
    prompt = sum(int(chat.get("gen_ai.usage.input_tokens", 0)) for chat in chats)
    completion = sum(int(chat.get("gen_ai.usage.output_tokens", 0)) for chat in chats)
    return {
        "seconds": f"{seconds:.3f}",
        "requests": f"{len(chats)}",
        "prompt_tokens": f"{prompt}",
        "completion_tokens": f"{completion}",
        "tools": f"{sum(operation(span) == 'execute_tool' for span in trace)}",
        "error": f"{(root.attributes or {}).get('error.type', '')}",
    }
