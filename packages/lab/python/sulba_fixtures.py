"""The fixtures a session's tests can ask for: `loop`, an event loop on a virtual clock (decision
record 21), `typecheck`, mypy's errors in the session's files (decision record 22), and `model`, a
model server that answers with the replies the test scripts (decision record 31).

The runner loads this module as a pytest plugin. A test that runs the learner's own tests with
pytest's pytester loads it in that run too, so their tests can ask for the same fixtures:
`pytester.runpytest("-p", "sulba_fixtures")`.
"""

from __future__ import annotations

import asyncio
import functools
import gc
import json
import math
import sys
import tempfile
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    import httpx

# mypy's options for a session's files: --strict, with no config file, as if on Linux, so the
# browser, a learner's machine and CI report the same errors (decision record 22).
MYPY_OPTIONS = ["--strict", "--config-file=", "--platform", "linux", "--no-error-summary"]


@functools.cache
def mypy_cache() -> str:
    """A folder for mypy's cache that lasts as long as the runner, so a check after the first
    reads what hasn't changed from it."""
    return tempfile.mkdtemp(prefix="sulba-mypy-")


def check_types(*files: str) -> list[str]:
    """mypy's errors in these files, each line as mypy prints it, such as
    `shapes.py:4: error: Function is missing a type annotation  [no-untyped-def]`."""
    from mypy import api

    # mypy raises the recursion limit and the garbage collector's thresholds for its own work,
    # and leaves them so. The session's code runs with Python's own.
    limit, thresholds = sys.getrecursionlimit(), gc.get_threshold()
    try:
        report, errors, _ = api.run([*MYPY_OPTIONS, "--cache-dir", mypy_cache(), *files])
    finally:
        sys.setrecursionlimit(limit)
        gc.set_threshold(*thresholds)
    if errors:
        raise RuntimeError(errors.strip())
    return report.splitlines()


class VirtualClockLoop(asyncio.BaseEventLoop):
    """An event loop whose clock jumps to its next timer instead of waiting for it.

    A test of asyncio code takes only as long as the code's own work, however long it sleeps,
    and the loop's time is the same in Pyodide and CPython. Pyodide's own loop can't run a
    coroutine to completion from a test, and asyncio's selector loop needs sockets that Pyodide
    doesn't have, so this loop waits on no I/O at all.
    """

    def __init__(self) -> None:
        super().__init__()
        self._now = 0.0
        # BaseEventLoop waits for its next timer by calling self._selector.select(timeout).
        self._selector = self

    def time(self) -> float:
        return self._now

    def select(self, timeout: float | None) -> list[Any]:
        # No timer to wait for, and no I/O to wake a task: the code waits forever.
        if timeout is None:
            raise RuntimeError("Every task is waiting on something that never happens.")
        self._now += timeout
        return []

    def _process_events(self, event_list: list[Any]) -> None:
        pass

    def _write_to_self(self) -> None:
        pass

    def run_forever(self) -> None:
        with self._alone():
            super().run_forever()

    def run_until_complete(self, future: Any) -> Any:
        with self._alone():
            return super().run_until_complete(future)

    @contextmanager
    def _alone(self) -> Iterator[None]:
        """Pyodide's loop counts as running from the moment it's made, and asyncio refuses to
        run a loop while another one is running, so it's set aside until this one stops."""
        running = asyncio._get_running_loop()
        asyncio._set_running_loop(None)
        try:
            yield
        finally:
            asyncio._set_running_loop(running)


@contextmanager
def threads_on_the_loop() -> Iterator[None]:
    """While a test runs, the work anyio would hand to a worker thread runs on the loop instead.

    Starlette, and so FastAPI, run a `def` endpoint or dependency in anyio's worker threads.
    A VirtualClockLoop waits on no thread, and Pyodide has none, so the work runs where the
    test's coroutine runs, with the same result. anyio is imported by then, by the app the test
    imports, or not used at all."""
    to_thread = sys.modules.get("anyio.to_thread")
    if to_thread is None:
        yield
        return
    in_a_thread = to_thread.run_sync

    async def run_sync(func: Callable[..., Any], *args: Any, **_: Any) -> Any:
        return func(*args)

    to_thread.run_sync = run_sync
    try:
        yield
    finally:
        to_thread.run_sync = in_a_thread


@pytest.fixture
def loop() -> Iterator[VirtualClockLoop]:
    """A new VirtualClockLoop for the test, whose time starts at 0. Afterwards, as asyncio.run
    does, the tasks left waiting are cancelled before the loop closes."""
    loop = VirtualClockLoop()
    with threads_on_the_loop():
        try:
            yield loop
        finally:
            waiting = asyncio.all_tasks(loop)
            for task in waiting:
                task.cancel()
            if waiting:
                loop.run_until_complete(asyncio.gather(*waiting, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()


@pytest.fixture
def typecheck() -> Callable[..., list[str]]:
    """typecheck("shapes.py") gives mypy's errors in the session's file under --strict, one line
    each, the same in Pyodide and CPython."""
    return check_types


# The type of error llama.cpp's llama-server names for each status it answers with (b11734,
# tools/server/server-common.cpp).
ERROR_TYPES = {
    400: "invalid_request_error",
    401: "authentication_error",
    403: "permission_error",
    404: "not_found_error",
    500: "server_error",
    501: "not_supported_error",
    503: "unavailable_error",
}


@dataclass(frozen=True)
class Received:
    """A request the scripted model received. Its headers' names are in lower case, and its body
    is the JSON it carried, or its text where it carried no JSON."""

    method: str
    path: str
    headers: dict[str, str]
    body: Any


class NoReplyLeft(BaseException):
    """The code sent the scripted model a request the test scripted no reply for. It isn't an
    Exception, so code that handles errors can't hide it."""


@dataclass(frozen=True)
class Scripted:
    """What the model does with one request: reply after a while, fail with a status, never
    answer (after is infinite), or drop the connection."""

    after: float
    id: str = ""
    pieces: tuple[str, ...] = ()
    calls: tuple[tuple[str, str, tuple[str, ...]], ...] = ()
    finish_reason: str = "stop"
    usage: tuple[int, int] = (0, 0)
    status: int = 200
    message: str = ""
    retry_after: int | None = None
    drops: bool = False


class ScriptedModel:
    """A model server that answers each chat request with the next reply the test scripted, in
    the form OpenAI's chat completions API and llama.cpp's llama-server give it (decision record
    31). Code reaches it through httpx, or the openai package, which is built on it:

        model.says("We open at 9.")
        assert ask(model.client(), "When do you open?") == "We open at 9."
        assert model.requests[0].body["messages"][-1]["content"] == "When do you open?"

    A request that asks for a stream gets the reply as server-sent events. Time passes only for
    an async client, on the loop's clock: a reply scripted to come after a while comes then, and
    a client whose read timeout is shorter raises httpx.ReadTimeout when the timeout ends. A sync
    client waits for nothing, but raises httpx.ReadTimeout all the same for a reply slower than
    its read timeout.
    """

    url = "http://model.test/v1"

    def __init__(self) -> None:
        self.requests: list[Received] = []
        self._script: deque[Scripted] = deque()
        self._answer: Callable[[Received], None] | None = None
        self._replies = 0
        self._calls = 0
        self._used = 0

    def says(
        self,
        *pieces: str,
        tool_calls: Sequence[tuple[str, Any]] = (),
        finish_reason: str | None = None,
        usage: tuple[int, int] = (0, 0),
        after: float = 0,
    ) -> None:
        """Script the next reply: its text, in the pieces a stream sends it in, and the tools it
        calls, each a name with its arguments as a dict, as the JSON text to send, or as that
        text's pieces. It finishes for "tool_calls" when it calls a tool and for "stop" when it
        doesn't, unless finish_reason says otherwise, such as "length". usage is the number of
        tokens in the prompt and in the reply, and after is how many seconds the reply takes."""
        calls = []
        for name, arguments in tool_calls:
            self._calls += 1
            if isinstance(arguments, str):
                parts: tuple[str, ...] = (arguments,)
            elif isinstance(arguments, dict):
                parts = (json.dumps(arguments, ensure_ascii=False, separators=(",", ":")),)
            else:
                parts = tuple(arguments)
            calls.append((f"call_{self._calls}", name, parts))
        self._replies += 1
        default = "tool_calls" if calls else "stop"
        self._script.append(
            Scripted(
                after=after,
                id=f"chatcmpl-{self._replies}",
                pieces=pieces,
                calls=tuple(calls),
                finish_reason=finish_reason or default,
                usage=usage,
            )
        )

    def fails(
        self, status: int, message: str, *, retry_after: int | None = None, after: float = 0
    ) -> None:
        """Script the next reply as an error: its status, and the message its body carries, as
        llama-server words an error. retry_after, in seconds, adds a Retry-After header."""
        self._script.append(
            Scripted(after=after, status=status, message=message, retry_after=retry_after)
        )

    def hangs(self) -> None:
        """Script the next request as one the model never answers. A client with a read timeout
        raises httpx.ReadTimeout when it ends."""
        self._script.append(Scripted(after=math.inf))

    def disconnects(self) -> None:
        """Script the next request as one the model drops without a reply, so the client raises
        httpx.RemoteProtocolError."""
        self._script.append(Scripted(after=0, drops=True))

    def answers(self, function: Callable[[Received], None]) -> None:
        """Have function script the answer to each request the test scripted none for. It's
        given the request, and scripts with says, fails, hangs or disconnects."""
        self._answer = function

    def client(self, **options: Any) -> httpx.Client:
        """An httpx.Client whose base_url is the model's API. options go to httpx.Client."""
        import httpx

        transport = httpx.MockTransport(self._handle)
        return httpx.Client(base_url=self.url, transport=transport, **options)

    def async_client(self, **options: Any) -> httpx.AsyncClient:
        """An httpx.AsyncClient whose base_url is the model's API. options go to
        httpx.AsyncClient."""
        import httpx

        transport = httpx.MockTransport(self._handle_async)
        return httpx.AsyncClient(base_url=self.url, transport=transport, **options)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        import httpx

        found = self._receive(request)
        if not isinstance(found, Scripted):
            return found
        timeout = request.extensions.get("timeout", {}).get("read")
        if timeout is not None and found.after > timeout:
            raise httpx.ReadTimeout("timed out", request=request)
        if math.isinf(found.after):
            raise RuntimeError("The model never answers, and the client has no read timeout.")
        return self._respond(found, request)

    async def _handle_async(self, request: httpx.Request) -> httpx.Response:
        import httpx

        found = self._receive(request)
        if not isinstance(found, Scripted):
            return found
        timeout = request.extensions.get("timeout", {}).get("read")
        if timeout is not None and found.after > timeout:
            await asyncio.sleep(timeout)
            raise httpx.ReadTimeout("timed out", request=request)
        if math.isinf(found.after):
            await asyncio.get_running_loop().create_future()
        await asyncio.sleep(found.after)
        return self._respond(found, request)

    def _receive(self, request: httpx.Request) -> Scripted | httpx.Response:
        """Keep the request, and find what the model does with it: an error for a request the
        API doesn't serve or a body llama-server would refuse, and the next answer otherwise."""
        text = request.content.decode(errors="replace")
        try:
            body: Any = json.loads(text)
            refused = refusal(body)
        except json.JSONDecodeError as error:
            body, refused = text, f"The request's body isn't JSON: {error}"
        headers = {name.lower(): value for name, value in request.headers.items()}
        received = Received(request.method, request.url.path, headers, body)
        self.requests.append(received)
        if (request.method, request.url.path) != ("POST", "/v1/chat/completions"):
            return error_response(404, "File Not Found")
        if refused:
            return error_response(400, refused)
        if not self._script and self._answer is not None:
            self._answer(received)
        if not self._script:
            raise NoReplyLeft(f"The test scripted no reply for request {self._used + 1}.")
        self._used += 1
        return self._script.popleft()

    def _respond(self, found: Scripted, request: httpx.Request) -> httpx.Response:
        import httpx

        if found.drops:
            message = "Server disconnected without sending a response."
            raise httpx.RemoteProtocolError(message, request=request)
        if found.status != 200:
            return error_response(found.status, found.message, found.retry_after)
        body = json.loads(request.content)
        name = body["model"] if isinstance(body.get("model"), str) else "scripted"
        prompt, completion = found.usage
        usage = {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
        }
        if body.get("stream") is not True:
            message: dict[str, Any] = {
                "role": "assistant",
                "content": "".join(found.pieces) if found.pieces else None,
            }
            if found.calls:
                message["tool_calls"] = [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {"name": tool, "arguments": "".join(parts)},
                    }
                    for call_id, tool, parts in found.calls
                ]
            choice = {"index": 0, "message": message, "finish_reason": found.finish_reason}
            reply = {
                "id": found.id,
                "object": "chat.completion",
                "created": 0,
                "model": name,
                "choices": [choice],
                "usage": usage,
            }
            return httpx.Response(200, json=reply)
        options = body.get("stream_options")
        include_usage = isinstance(options, dict) and options.get("include_usage") is True
        events = streamed(found, name, usage if include_usage else None)
        text = "".join(f"data: {compact(event)}\n\n" for event in events)
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            content=f"{text}data: [DONE]\n\n".encode(),
        )


def refusal(body: Any) -> str | None:
    """Why llama-server would refuse a chat request with this body, in its words (b11734,
    tools/server/server-common.cpp), or None."""
    if not isinstance(body, dict) or "messages" not in body:
        return "'messages' is required"
    if not isinstance(body["messages"], list):
        return "Expected 'messages' to be an array"
    for message in body["messages"]:
        fields = message if isinstance(message, dict) else {}
        if fields.get("role") != "assistant" and "content" not in fields:
            return "All non-assistant messages must contain 'content'"
        if fields.get("role") == "assistant" and not {"content", "tool_calls"} & fields.keys():
            return "Assistant message must contain either 'content' or 'tool_calls'!"
    return None


def error_response(status: int, message: str, retry_after: int | None = None) -> httpx.Response:
    """An error in llama-server's form: its status, message and, where it names one, type."""
    import httpx

    error: dict[str, Any] = {"code": status, "message": message}
    if status in ERROR_TYPES:
        error["type"] = ERROR_TYPES[status]
    headers = {} if retry_after is None else {"Retry-After": str(retry_after)}
    return httpx.Response(status, json={"error": error}, headers=headers)


def streamed(found: Scripted, name: str, usage: dict[str, int] | None) -> list[dict[str, Any]]:
    """The chunks a reply streams in, as llama-server sends them: the role, each piece of the
    text, each tool call's name and then its arguments' pieces, the reason it finished, and, when
    the request asks for it, the tokens it used."""

    def chunk(choices: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": found.id,
            "object": "chat.completion.chunk",
            "created": 0,
            "model": name,
            "choices": choices,
        }

    deltas: list[dict[str, Any]] = [{"role": "assistant", "content": None}]
    deltas += [{"content": piece} for piece in found.pieces if piece]
    for index, (call_id, tool, parts) in enumerate(found.calls):
        call = {"index": index, "id": call_id, "type": "function", "function": {"name": tool}}
        deltas.append({"tool_calls": [call]})
        deltas += [
            {"tool_calls": [{"index": index, "function": {"arguments": part}}]}
            for part in parts
            if part
        ]
    events = [chunk([{"index": 0, "delta": delta, "finish_reason": None}]) for delta in deltas]
    events.append(chunk([{"index": 0, "delta": {}, "finish_reason": found.finish_reason}]))
    if usage is not None:
        events.append({**chunk([]), "usage": usage})
    return events


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


@pytest.fixture
def model() -> ScriptedModel:
    """A ScriptedModel for the test, with no reply scripted yet."""
    return ScriptedModel()
