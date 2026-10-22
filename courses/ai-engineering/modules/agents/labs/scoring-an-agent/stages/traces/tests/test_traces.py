import httpx
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from traces import Traced, agent, runs, tool

MODEL = "Qwen3.5-4B"
BODY = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "When does the DMV open?"}],
    "max_tokens": 768,
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 20,
    "presence_penalty": 1.5,
    "seed": 41,
}


@pytest.fixture
def traced():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("desk"), exporter


def search(name, arguments):
    if arguments == "{}":
        raise ValueError("search_help needs a query.")
    return "[p17] Offices open at 8:30."


@pytest.mark.id("tst_uvnge4")
def test_a_chat_request(model, traced):
    """A chat request's span: what it asked for and what came back"""
    tracer, exporter = traced
    model.says(tool_calls=[("search_help", {"query": "DMV hours"})], usage=(3120, 41))
    response = Traced(model.client(), tracer).post("/chat/completions", json=BODY)
    assert response.json()["choices"][0]["finish_reason"] == "tool_calls"
    (span,) = exporter.get_finished_spans()
    assert span.name == f"chat {MODEL}"
    assert span.kind == SpanKind.CLIENT
    assert span.status.status_code == StatusCode.UNSET
    assert dict(span.attributes) == {
        "gen_ai.operation.name": "chat",
        "gen_ai.provider.name": "llama.cpp",
        "gen_ai.request.model": MODEL,
        "gen_ai.request.max_tokens": 768,
        "gen_ai.request.temperature": 0.7,
        "gen_ai.request.top_p": 0.8,
        "gen_ai.request.top_k": 20,
        "gen_ai.request.presence_penalty": 1.5,
        "gen_ai.request.seed": 41,
        "server.address": "model.test",
        "server.port": 80,
        "gen_ai.response.id": "chatcmpl-1",
        "gen_ai.response.model": MODEL,
        "gen_ai.response.finish_reasons": ("tool_calls",),
        "gen_ai.usage.input_tokens": 3120,
        "gen_ai.usage.output_tokens": 41,
    }


@pytest.mark.id("tst_b5unxr")
def test_a_request_that_fails(model, traced):
    """An error status or a dropped connection ends the request's span in an error, with its
    type"""
    tracer, exporter = traced
    client = Traced(model.client(), tracer)
    model.fails(503, "Loading model")
    assert (
        client.post(
            "/chat/completions", json={"model": MODEL, "messages": []}
        ).status_code
        == 503
    )
    model.disconnects()
    with pytest.raises(httpx.RemoteProtocolError):
        client.post("/chat/completions", json={"model": MODEL, "messages": []})
    refused, dropped = exporter.get_finished_spans()
    for span, kind in ((refused, "503"), (dropped, "RemoteProtocolError")):
        assert span.status.status_code == StatusCode.ERROR
        assert span.attributes["error.type"] == kind
        assert "gen_ai.usage.input_tokens" not in span.attributes
    assert (
        "server.address" in refused.attributes
        and "gen_ai.request.seed" not in refused.attributes
    )


@pytest.mark.id("tst_vik9lt")
def test_a_tool(traced):
    """A tool's span, current while it runs, and its error when it raises one"""
    tracer, exporter = traced
    seen = []

    def call(name, arguments):
        seen.append(trace.get_current_span().name)
        return search(name, arguments)

    traced_search = tool(tracer, call)
    assert (
        traced_search("search_help", '{"query": "DMV hours"}')
        == "[p17] Offices open at 8:30."
    )
    with pytest.raises(ValueError):
        traced_search("search_help", "{}")
    assert seen == ["execute_tool search_help"] * 2
    done, failed = exporter.get_finished_spans()
    assert done.kind == SpanKind.INTERNAL
    assert dict(done.attributes) == {
        "gen_ai.operation.name": "execute_tool",
        "gen_ai.tool.name": "search_help",
        "gen_ai.tool.type": "function",
    }
    assert done.status.status_code == StatusCode.UNSET
    assert failed.status.status_code == StatusCode.ERROR
    assert failed.attributes["error.type"] == "ValueError"


@pytest.mark.id("tst_7d8gh0")
def test_an_agents_run(model, traced):
    """The agent's span holds the run's requests and tools"""
    tracer, exporter = traced
    client = Traced(model.client(), tracer)
    traced_search = tool(tracer, search)
    model.says(tool_calls=[("search_help", {"query": "DMV hours"})], usage=(3120, 41))
    model.says("Offices open at 8:30 [p17].", usage=(3240, 12))
    with agent(tracer, "desk", MODEL) as span:
        assert trace.get_current_span() is span
        client.post("/chat/completions", json=BODY)
        traced_search("search_help", '{"query": "DMV hours"}')
        client.post("/chat/completions", json=BODY)
    chat, search_span, reply, run = exporter.get_finished_spans()
    assert run.name == "invoke_agent desk"
    assert run.kind == SpanKind.INTERNAL
    assert dict(run.attributes) == {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.provider.name": "llama.cpp",
        "gen_ai.agent.name": "desk",
        "gen_ai.request.model": MODEL,
    }
    for span in (chat, search_span, reply):
        assert span.parent.span_id == run.context.span_id
    (row,) = runs(exporter.get_finished_spans())
    assert {key: value for key, value in row.items() if key != "seconds"} == {
        "requests": "2",
        "prompt_tokens": "6360",
        "completion_tokens": "53",
        "tools": "1",
        "error": "",
    }


@pytest.mark.id("tst_dddblg")
def test_runs_from_spans(traced):
    """A row for each trace an agent's span begins, in the order they began, with every span
    beneath it, a sub-agent's too"""
    tracer, exporter = traced
    second = 1_000_000_000

    def span(name, operation, begins, ends, parent=None, **attributes):
        context = trace.set_span_in_context(parent) if parent else None
        made = tracer.start_span(
            name,
            context=context,
            attributes={"gen_ai.operation.name": operation, **attributes},
            start_time=begins * second,
        )
        made.end(end_time=ends * second)
        return made

    def run(begins):
        return tracer.start_span(
            "invoke_agent desk",
            attributes={"gen_ai.operation.name": "invoke_agent"},
            start_time=begins * second,
        )

    later = run(100)
    usage = {"gen_ai.usage.input_tokens": 2000, "gen_ai.usage.output_tokens": 30}
    span("chat m", "chat", 100, 104, later, **usage)
    span("execute_tool search_help", "execute_tool", 104, 105, later)
    researcher = tracer.start_span(
        "invoke_agent researcher",
        context=trace.set_span_in_context(later),
        attributes={"gen_ai.operation.name": "invoke_agent"},
        start_time=105 * second,
    )
    span("chat m", "chat", 105, 109, researcher, **usage)
    researcher.end(end_time=110 * second)
    later.end(end_time=161 * second + 500_000_000)
    earlier = run(10)
    span("chat m", "chat", 10, 12, earlier, **{"gen_ai.usage.input_tokens": 900})
    earlier.set_attribute("error.type", "OutOfRounds")
    earlier.end(end_time=20 * second)
    span("chat m", "chat", 30, 31)
    assert runs(exporter.get_finished_spans()) == [
        {
            "seconds": "10.000",
            "requests": "1",
            "prompt_tokens": "900",
            "completion_tokens": "0",
            "tools": "0",
            "error": "OutOfRounds",
        },
        {
            "seconds": "61.500",
            "requests": "2",
            "prompt_tokens": "4000",
            "completion_tokens": "60",
            "tools": "1",
            "error": "",
        },
    ]


@pytest.mark.id("tst_xm1lt5")
def test_a_run_that_fails(model, traced):
    """A run that raises ends the agent's span in an error, with its type"""
    tracer, exporter = traced
    client = Traced(model.client(), tracer)
    model.fails(503, "Loading model")
    with pytest.raises(httpx.HTTPStatusError), agent(tracer, "desk", MODEL):
        client.post("/chat/completions", json=BODY).raise_for_status()
    refused, run = exporter.get_finished_spans()
    assert run.status.status_code == StatusCode.ERROR
    assert run.attributes["error.type"] == "HTTPStatusError"
    (row,) = runs(exporter.get_finished_spans())
    assert row["error"] == "HTTPStatusError"
    assert row["requests"] == "1"
