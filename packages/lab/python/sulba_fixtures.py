"""The fixtures a session's tests can ask for: `loop`, an event loop on a virtual clock (decision
record 21), `typecheck`, mypy's errors in the session's files (decision record 22), `model`, a
model server that answers with the replies the test scripts (decision record 31), `identity`, an
OpenID provider that signs the test's people in (decision record 38), and on the learner's
machine `database`, a new Postgres database with pgvector (decision record 33), and `spark`, a
Spark session on Sail (decision record 41).

The runner loads this module as a pytest plugin. A test that runs the learner's own tests with
pytest's pytester loads it in that run too, so their tests can ask for the same fixtures:
`pytester.runpytest("-p", "sulba_fixtures")`.
"""

from __future__ import annotations

import asyncio
import base64
import functools
import gc
import importlib.util
import json
import math
import os
import secrets
import shutil
import struct
import sys
import tempfile
from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    import httpx

# How CI's Spark job asks the spark fixture for Spark itself, in place of Sail (decision record 41).
SPARK = os.environ.get("SULBA_SPARK", "sail")
# PySpark's testing helpers exit when they can't find SPARK_HOME, which only Spark itself has, so
# with Sail it names the folder of PySpark's client, before a test file imports them.
if SPARK == "sail" and (pyspark := importlib.util.find_spec("pyspark")) is not None:
    os.environ.setdefault("SPARK_HOME", str(Path(pyspark.origin or "").parent))

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
    """A request the scripted model or provider received. Its headers' names are in lower case,
    and its body is the JSON it carried, a form's fields, or its text where it carried neither."""

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
    probabilities: tuple[tuple[tuple[str, float], ...], ...] = ()
    calls: tuple[tuple[str, str, tuple[str, ...]], ...] = ()
    finish_reason: str = "stop"
    usage: tuple[int, int] = (0, 0)
    status: int = 200
    message: str = ""
    retry_after: int | None = None
    drops: bool = False

    @property
    def failure(self) -> bool:
        """Whether it fails, hangs or drops the connection rather than reply."""
        return self.status != 200 or self.drops or math.isinf(self.after)


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

    It answers a completion request, a prompt to go on from, with the next reply too, and gives
    a request that asks for logprobs each token's probability and the likeliest tokens for its
    place, from the probabilities the test scripted:

        model.says("No", probabilities=[{"No": 0.9, "Yes": 0.1}])

    It embeds text and reranks documents too, as an embedding or reranking model does, with the
    vectors and scores the test gives it:

        model.embeds({"When do you open?": [0.6, 0.8]})
        model.ranks(lambda query, document: 1.0 if "open" in document else 0.0)

    A failure the test scripts with fails, hangs or disconnects answers the next request,
    whatever it asks for.
    """

    url = "http://model.test/v1"

    def __init__(self) -> None:
        self.requests: list[Received] = []
        self._script: deque[Scripted] = deque()
        self._answer: Callable[[Received], None] | None = None
        self._vectors: Callable[[str], Sequence[float]] | None = None
        self._scores: Callable[[str, str], float] | None = None
        self._tokens: Callable[[str], int] = no_tokens
        self._vocabulary: dict[str, int] = {}
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
        probabilities: Sequence[Mapping[str, float]] = (),
    ) -> None:
        """Script the next reply: its text, in the pieces a stream sends it in, and the tools it
        calls, each a name with its arguments as a dict, as the JSON text to send, or as that
        text's pieces. It finishes for "tool_calls" when it calls a tool and for "stop" when it
        doesn't, unless finish_reason says otherwise, such as "length". usage is the number of
        tokens in the prompt and in the reply, and after is how many seconds the reply takes.
        probabilities gives each piece, as a token, the tokens the model weighed for its place
        and their probabilities, the piece among them, for a request that asks for logprobs."""
        if probabilities and len(probabilities) != len(pieces):
            raise ValueError("probabilities gives one mapping of tokens for each piece.")
        for piece, weighed in zip(pieces, probabilities, strict=bool(probabilities)):
            if piece not in weighed:
                raise ValueError(f"The tokens weighed for {piece!r} leave it out.")
            if not all(0 < probability <= 1 for probability in weighed.values()):
                raise ValueError("Each probability is above 0 and at most 1.")
            for token in weighed:
                self._vocabulary.setdefault(token, len(self._vocabulary))
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
                probabilities=tuple(tuple(weighed.items()) for weighed in probabilities),
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
        """Have function script the answer to each chat or completion request the test scripted
        none for. It's given the request, and scripts with says, fails, hangs or disconnects."""
        self._answer = function

    def embeds(
        self,
        vectors: Mapping[str, Sequence[float]] | Callable[[str], Sequence[float]],
        *,
        tokens: Callable[[str], int] | None = None,
    ) -> None:
        """Have the model embed each text with the vector vectors gives it, from a mapping of
        texts or a function of one, in every embeddings request from now on. A text a mapping has
        no vector for raises NoReplyLeft. tokens counts a text's tokens for the reply's usage,
        which is 0 without it."""
        if isinstance(vectors, Mapping):
            known = vectors

            def vector(text: str) -> Sequence[float]:
                if text not in known:
                    raise NoReplyLeft(f"The test scripted no vector for {text!r}.")
                return known[text]

            self._vectors = vector
        else:
            self._vectors = vectors
        self._tokens = tokens or no_tokens

    def ranks(self, scores: Mapping[tuple[str, str], float] | Callable[[str, str], float]) -> None:
        """Have the model score each document for a query with scores, from a mapping of
        (query, document) pairs or a function of them, in every rerank request from now on. A
        pair a mapping has no score for raises NoReplyLeft."""
        if isinstance(scores, Mapping):
            known = scores

            def score(query: str, document: str) -> float:
                if (query, document) not in known:
                    raise NoReplyLeft(f"The test scripted no score for {document!r}.")
                return known[query, document]

            self._scores = score
        else:
            self._scores = scores

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
        API doesn't serve or a body llama-server would refuse, a failure the test scripted, and
        the answer otherwise."""
        text = request.content.decode(errors="replace")
        headers = {name.lower(): value for name, value in request.headers.items()}
        endpoint = ENDPOINTS.get((request.method, request.url.path))
        try:
            body: Any = json.loads(text)
            refused = REFUSALS[endpoint](body) if endpoint else None
        except json.JSONDecodeError as error:
            body, refused = text, f"The request's body isn't JSON: {error}"
        received = Received(request.method, request.url.path, headers, body)
        self.requests.append(received)
        if endpoint is None:
            return error_response(404, "File Not Found")
        if refused:
            return error_response(400, refused)
        if endpoint not in ("chat", "completions"):
            if self._script and self._script[0].failure:
                self._used += 1
                return self._script.popleft()
            return self._embedded(body) if endpoint == "embeddings" else self._ranked(body)
        if not self._script and self._answer is not None:
            self._answer(received)
        if not self._script:
            raise NoReplyLeft(f"The test scripted no reply for request {self._used + 1}.")
        self._used += 1
        return self._script.popleft()

    def _embedded(self, body: dict[str, Any]) -> httpx.Response:
        """The embeddings of the request's texts, as llama-server gives them (b11734,
        tools/server/server-common.cpp, format_embeddings_response_oaicompat)."""
        import httpx

        if self._vectors is None:
            raise NoReplyLeft("The test scripted no embeddings: call model.embeds first.")
        texts = body["input"] if isinstance(body["input"], list) else [body["input"]]
        base64_wanted = body.get("encoding_format") == "base64"
        data = []
        for index, text in enumerate(texts):
            vector = [float(value) for value in self._vectors(text)]
            if base64_wanted:
                packed = struct.pack(f"<{len(vector)}f", *vector)
                item: dict[str, Any] = {
                    "embedding": base64.b64encode(packed).decode(),
                    "index": index,
                    "object": "embedding",
                    "encoding_format": "base64",
                }
            else:
                item = {"embedding": vector, "index": index, "object": "embedding"}
            data.append(item)
        used = sum(self._tokens(text) for text in texts)
        return httpx.Response(
            200,
            json={
                "model": body["model"] if isinstance(body.get("model"), str) else "scripted",
                "object": "list",
                "usage": {"prompt_tokens": used, "total_tokens": used},
                "data": data,
            },
        )

    def _ranked(self, body: dict[str, Any]) -> httpx.Response:
        """The documents' scores for the query, highest first and at most top_n of them, as
        llama-server gives them (b11734, tools/server/server-common.cpp,
        format_response_rerank): in Jina's form, or in TEI's when the request names them
        texts."""
        import httpx

        if self._scores is None:
            raise NoReplyLeft("The test scripted no scores: call model.ranks first.")
        tei = "texts" in body
        documents = documents_of(body)
        label = "score" if tei else "relevance_score"
        ranked = sorted(
            (
                {"index": index, label: float(self._scores(body["query"], document))}
                for index, document in enumerate(documents)
            ),
            key=lambda result: -result[label],
        )
        # llama-server reads top_n as an integer, truncating a number and taking a boolean as 1 or
        # 0, and keeps every document for anything else. It keeps none for a negative top_n.
        top_n = body.get("top_n")
        if not isinstance(top_n, int | float):
            top_n = len(documents)
        ranked = ranked[: max(0, int(top_n))]
        if tei:
            return httpx.Response(200, json=ranked)
        return httpx.Response(
            200,
            json={
                "model": body["model"] if isinstance(body.get("model"), str) else "scripted",
                "object": "list",
                "usage": {"prompt_tokens": 0, "total_tokens": 0},
                "results": ranked,
            },
        )

    def _logprobs(self, found: Scripted, weighed: Any, after_sampling: bool) -> Any:
        """Each token of the reply with its probability and those of the most likely tokens for
        its place, at most weighed of them, as llama-server gives them (b11734,
        tools/server/server-task.cpp, probs_vector_to_json): as logarithms, or as probabilities
        when the request asks for them after sampling. None when the request asks for none."""
        if isinstance(weighed, bool) or not isinstance(weighed, int) or weighed <= 0:
            return None
        if not found.probabilities:
            raise NoReplyLeft(
                "The request asks for logprobs, and the test scripted no probabilities: "
                "give says probabilities."
            )
        field, top = ("prob", "top_probs") if after_sampling else ("logprob", "top_logprobs")

        def token(text: str, probability: float) -> dict[str, Any]:
            value = probability if after_sampling else math.log(probability)
            return {
                "id": self._vocabulary[text],
                "token": text,
                "bytes": list(text.encode()),
                field: value,
            }

        content = []
        for piece, tokens in zip(found.pieces, found.probabilities, strict=True):
            likeliest = sorted(tokens, key=lambda item: -item[1])[:weighed]
            content.append(
                {**token(piece, dict(tokens)[piece]), top: [token(*item) for item in likeliest]}
            )
        return {"content": content}

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
        completing = ENDPOINTS[request.method, request.url.path] == "completions"
        if completing:
            weighed = body.get("n_probs", body.get("logprobs", 0))
        elif body.get("logprobs") is True:
            weighed = 20 if body.get("top_logprobs") is None else body["top_logprobs"]
        else:
            weighed = 0
        logprobs = self._logprobs(found, weighed, body.get("post_sampling_probs") is True)
        if completing:
            if found.calls:
                raise ValueError("A completion calls no tools: script tool calls for chat.")
            text = {
                "text": "".join(found.pieces),
                "index": 0,
                "logprobs": logprobs,
                "finish_reason": found.finish_reason,
            }
            reply = {
                "choices": [text],
                "created": 0,
                "model": name,
                "object": "text_completion",
                "usage": usage,
                "id": found.id,
            }
            return httpx.Response(200, json=reply)
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
            if logprobs is not None:
                choice["logprobs"] = logprobs
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


def no_tokens(text: str) -> int:
    return 0


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
    if body.get("logprobs") is True and body.get("stream") is True:
        if body.get("tools"):
            return "logprobs is not supported with tools + stream"
        return "The scripted model gives logprobs only with replies that aren't streamed."
    if body.get("logprobs") is not True and body.get("top_logprobs") is not None:
        return "top_logprobs requires logprobs to be set to true"
    return None


def completions_refusal(body: Any) -> str | None:
    """Why llama-server would refuse a completion request with this body, in its words (b11734,
    tools/server/server-context.cpp, handle_completions_impl), or None. The scripted model
    completes one prompt, given as text, and doesn't stream."""
    if not isinstance(body, dict) or "prompt" not in body:
        return "[json.exception.out_of_range.403] key 'prompt' not found"
    if not isinstance(body["prompt"], str):
        return "The scripted model completes one prompt, given as a string."
    if body.get("stream") is True:
        return "The scripted model streams only chat replies."
    return None


def embeddings_refusal(body: Any) -> str | None:
    """Why llama-server would refuse an embeddings request with this body, in its words
    (b11734, tools/server/server-context.cpp, handle_embeddings_impl), or None. The scripted
    model embeds only text, given as OpenAI's API gives it, not token ids or llama-server's own
    content form."""
    if isinstance(body, dict) and "input" not in body and "content" in body:
        return 'The scripted model embeds text given as "input", as OpenAI\'s API gives it.'
    if not isinstance(body, dict) or "input" not in body:
        return '"input" or "content" must be provided'
    if body.get("encoding_format", "float") not in ("float", "base64"):
        return "The format to return the embeddings in. Can be either float or base64"
    texts = body["input"] if isinstance(body["input"], list) else [body["input"]]
    if not texts:
        return '"input" must not be empty'
    if not all(isinstance(text, str) for text in texts):
        return "The scripted model embeds text, given as a string or a list of strings."
    return None


def rerank_refusal(body: Any) -> str | None:
    """Why llama-server would refuse a rerank request with this body, in its words (b11734,
    tools/server/server-context.cpp), or None."""
    if not isinstance(body, dict) or "query" not in body:
        return '"query" must be provided'
    if not isinstance(body["query"], str):
        return '"query" must be a string'
    if not documents_of(body):
        return '"documents" must be a non-empty string array'
    return None


def documents_of(body: dict[str, Any]) -> list[str]:
    """A rerank request's documents as llama-server reads them: its documents, unless they are
    missing or not a list of strings, then its texts on the same terms, and none otherwise."""
    for key in ("documents", "texts"):
        value = body.get(key)
        if isinstance(value, list) and all(isinstance(document, str) for document in value):
            return value
    return []


# The paths the scripted model serves, as llama-server serves them under /v1, and how it checks
# each one's requests.
ENDPOINTS = {
    ("POST", "/v1/chat/completions"): "chat",
    ("POST", "/v1/completions"): "completions",
    ("POST", "/v1/embeddings"): "embeddings",
    ("POST", "/v1/rerank"): "rerank",
    ("POST", "/v1/reranking"): "rerank",
}
REFUSALS: dict[str, Callable[[Any], str | None]] = {
    "chat": refusal,
    "completions": completions_refusal,
    "embeddings": embeddings_refusal,
    "rerank": rerank_refusal,
}


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


class ScriptedIdentity:
    """An OpenID provider that signs the test's people in, for code that signs its users in with
    OpenID Connect's authorization code flow and PKCE (decision record 38). The app reaches its
    discovery document, token endpoint, keys and userinfo through httpx, and the test plays the
    browser: it takes the app's redirect to the provider, signs a person in there, and follows
    the provider's redirect back to the app.

        back = identity.sign_in(redirect.headers["location"], "ada")
        callback = await client.get(back)

    It holds each request to the rules a provider keeps: a client it knows, at the redirect URI
    registered for it, asking for openid, with an S256 code challenge; and a code used once, by
    the client it was given to, with the same redirect URI and the verifier its challenge came
    from. Its ID tokens are JWTs it signs with RS256, with a key its keys endpoint publishes, and
    each lasts five minutes by the system's clock, as a token library reads it.

    For a test of code that must refuse a token, it makes tokens of any shape, and the token
    endpoint gives the next one scripted in place of its own:

        identity.returns(id_token=identity.id_token("ada", audience="another-app"))
    """

    issuer = "https://id.test"
    client_id = "desk"
    client_secret = "desk-client-secret"
    redirect_uri = "https://desk.test/auth/callback"

    def __init__(self) -> None:
        self.people: dict[str, dict[str, Any]] = {}
        self.requests: list[Received] = []
        self._keys = [("key-1", signing_key())]
        self._grants: dict[str, dict[str, Any]] = {}
        self._access: dict[str, dict[str, Any]] = {}
        self._script: deque[dict[str, Any]] = deque()
        self.person("ada", email="ada@example.com")
        self.person("grace", email="grace@example.com")

    def person(self, name: str, *, email: str, **claims: Any) -> None:
        """Someone who can sign in, by their name: their subject, `sub`, is "user-" and the name.
        Any other claims, such as `groups`, go in their ID tokens and their userinfo."""
        self.people[name] = {"sub": f"user-{name}", "email": email, "name": name.title(), **claims}

    def sign_in(self, url: str, name: str = "ada") -> str:
        """The address the provider sends the browser back to once the person signs in at url, the
        app's authorization request: the redirect URI with a code and the request's state. A
        request with no known client, or with a redirect URI not registered for it, raises
        ValueError, as a provider shows an error rather than redirect there; any other request
        that doesn't fit comes back with an error, as OAuth 2.0 sends one."""
        query = self._authorization(url)
        if query.get("code_challenge_method") != "S256" or not query.get("code_challenge"):
            return self._back(query, error="invalid_request")
        if "openid" not in query.get("scope", "").split() or query.get("response_type") != "code":
            return self._back(query, error="invalid_request")
        code = secrets.token_urlsafe(24)
        self._grants[code] = {
            "person": name,
            "challenge": query["code_challenge"],
            "nonce": query.get("nonce"),
            "redirect_uri": query["redirect_uri"],
        }
        return self._back(query, code=code)

    def declines(self, url: str) -> str:
        """The address the provider sends the browser back to when the person won't sign in."""
        return self._back(self._authorization(url), error="access_denied")

    def id_token(
        self,
        name: str = "ada",
        *,
        nonce: str | None = None,
        audience: str | None = None,
        issuer: str | None = None,
        lasts: int = 300,
        stranger: bool = False,
    ) -> str:
        """An ID token for the person, as the provider signs one, or with the audience, issuer,
        lifetime in seconds, from now, that the test gives. A stranger's token is signed with a
        key the provider doesn't publish."""
        import time

        now = int(time.time())
        claims = {
            **self.people[name],
            "iss": issuer or self.issuer,
            "aud": audience or self.client_id,
            "iat": now,
            "exp": now + lasts,
        }
        if nonce is not None:
            claims["nonce"] = nonce
        kid, key = ("stranger", signing_key("stranger")) if stranger else self._keys[-1]
        return signed_jwt(claims, kid, key)

    def returns(self, **response: Any) -> None:
        """Script the token endpoint's next answer to a request that fits, in place of its own:
        an access token, its type and lifetime are added where the test doesn't give them."""
        self._script.append(response)

    def rotate(self) -> None:
        """Sign with a new key from now on, published beside the old one."""
        self._keys.append((f"key-{len(self._keys) + 1}", signing_key(str(len(self._keys)))))

    def client(self, **options: Any) -> httpx.Client:
        """An httpx.Client whose base_url is the provider. options go to httpx.Client."""
        import httpx

        transport = httpx.MockTransport(self._handle)
        return httpx.Client(base_url=self.issuer, transport=transport, **options)

    def async_client(self, **options: Any) -> httpx.AsyncClient:
        """An httpx.AsyncClient whose base_url is the provider. options go to
        httpx.AsyncClient."""
        import httpx

        async def handle(request: httpx.Request) -> httpx.Response:
            return self._handle(request)

        transport = httpx.MockTransport(handle)
        return httpx.AsyncClient(base_url=self.issuer, transport=transport, **options)

    def _authorization(self, url: str) -> dict[str, str]:
        from urllib.parse import parse_qsl, urlsplit

        split = urlsplit(url)
        if f"{split.scheme}://{split.netloc}{split.path}" != f"{self.issuer}/authorize":
            raise ValueError(f"{url} isn't the provider's authorization endpoint.")
        query = dict(parse_qsl(split.query))
        if query.get("client_id") != self.client_id:
            raise ValueError("The provider knows no client by that id.")
        if query.get("redirect_uri") != self.redirect_uri:
            raise ValueError("The redirect URI isn't the one registered for the client.")
        return query

    def _back(self, query: Mapping[str, str], **answer: str) -> str:
        from urllib.parse import urlencode

        if "state" in query:
            answer["state"] = query["state"]
        return f"{query['redirect_uri']}?{urlencode(answer)}"

    def _handle(self, request: httpx.Request) -> httpx.Response:
        from urllib.parse import parse_qsl

        import httpx

        text = request.content.decode()
        body: Any = dict(parse_qsl(text)) if request.method == "POST" else text
        headers = {name.lower(): value for name, value in request.headers.items()}
        self.requests.append(Received(request.method, request.url.path, headers, body))
        path = request.url.path
        if request.method == "GET" and path == "/.well-known/openid-configuration":
            return httpx.Response(200, json=self._discovery())
        if request.method == "GET" and path == "/keys":
            return httpx.Response(200, json={"keys": [jwk(kid, key) for kid, key in self._keys]})
        if request.method == "POST" and path == "/token":
            return self._token(headers, body)
        if request.method == "GET" and path == "/userinfo":
            return self._userinfo(headers)
        return httpx.Response(404, json={"error": "not_found"})

    def _discovery(self) -> dict[str, Any]:
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}/authorize",
            "token_endpoint": f"{self.issuer}/token",
            "jwks_uri": f"{self.issuer}/keys",
            "userinfo_endpoint": f"{self.issuer}/userinfo",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "email", "profile"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "code_challenge_methods_supported": ["S256"],
        }

    def _token(self, headers: Mapping[str, str], form: Mapping[str, str]) -> httpx.Response:
        import hashlib

        import httpx

        client = (form.get("client_id"), form.get("client_secret"))
        if headers.get("authorization", "").startswith("Basic "):
            pair = base64.b64decode(headers["authorization"][6:]).decode()
            client = tuple(pair.split(":", 1))  # type: ignore[assignment]
        if client != (self.client_id, self.client_secret):
            challenge = {"WWW-Authenticate": "Basic"}
            return httpx.Response(401, json={"error": "invalid_client"}, headers=challenge)
        if form.get("grant_type") != "authorization_code":
            return httpx.Response(400, json={"error": "unsupported_grant_type"})
        # A code is used once: a second request with it fails like one with no grant at all.
        grant = self._grants.pop(form.get("code", ""), None)
        verifier = form.get("code_verifier", "")
        challenge = base64url(hashlib.sha256(verifier.encode()).digest())
        if (
            grant is None
            or form.get("redirect_uri") != grant["redirect_uri"]
            or challenge != grant["challenge"]
        ):
            return httpx.Response(400, json={"error": "invalid_grant"})
        access_token = secrets.token_urlsafe(24)
        self._access[access_token] = grant
        answer = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 300,
            "id_token": self.id_token(grant["person"], nonce=grant["nonce"]),
        }
        if self._script:
            answer |= self._script.popleft()
        headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}
        return httpx.Response(200, json=answer, headers=headers)

    def _userinfo(self, headers: Mapping[str, str]) -> httpx.Response:
        import httpx

        token = headers.get("authorization", "").removeprefix("Bearer ")
        grant = self._access.get(token)
        if grant is None:
            # OAuth 2.0 gives a bearer token's error in the WWW-Authenticate header (RFC 6750).
            return httpx.Response(401, headers={"WWW-Authenticate": 'Bearer error="invalid_token"'})
        return httpx.Response(200, json=self.people[grant["person"]])


@functools.cache
def signing_key(name: str = "provider") -> Any:
    """An RSA key for signing ID tokens, made once a run for each name, since making one takes
    a moment."""
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def signed_jwt(claims: Mapping[str, Any], kid: str, key: Any) -> str:
    """The claims as a JWT, signed with RS256 by the key, which the kid names (RFC 7515)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    signing_input = ".".join(
        base64url(json.dumps(part, separators=(",", ":")).encode()) for part in (header, claims)
    )
    signature = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input}.{base64url(signature)}"


def jwk(kid: str, key: Any) -> dict[str, str]:
    """The key's public half as a JSON Web Key (RFC 7517 and RFC 7518)."""
    numbers = key.public_key().public_numbers()

    def octets(value: int) -> str:
        return base64url(value.to_bytes((value.bit_length() + 7) // 8, "big"))

    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": octets(numbers.n),
        "e": octets(numbers.e),
    }


@pytest.fixture
def identity() -> ScriptedIdentity:
    """A ScriptedIdentity for the test, with Ada and Grace among its people."""
    return ScriptedIdentity()


# pgvector for Linux comes from the PostgreSQL project's packages for Debian 12, which run on any
# processor of their kind: the pgvector embedded-postgres builds for Linux runs only on processors
# like the one that built it (decision record 33). Each package is pinned by its name, size and
# sha256, under the name Python gives the machine.
PGVECTOR_PACKAGES = "https://apt.postgresql.org/pub/repos/apt/pool/main/p/pgvector"
PGVECTOR_BUILDS = {
    "x86_64": (
        "postgresql-18-pgvector_0.8.7-1.pgdg12+1_amd64.deb",
        273916,
        "a47bf74b1b074ec9a2fad8acde8f7b1fe2b3e4c23028e866f7655965a41f4f25",
    ),
    "aarch64": (
        "postgresql-18-pgvector_0.8.7-1.pgdg12+1_arm64.deb",
        243408,
        "5eda70cc45cec0d5a09961b1bba918512b7300fc6bcd104124c2417e60867d40",
    ),
}
# Windows tells whether its processor has AVX2 by this feature's number.
PF_AVX2_INSTRUCTIONS_AVAILABLE = 40


class Postgres:
    """A Postgres server with pgvector for a run's tests, from the binaries the lab's project
    installs with embedded-postgres (decision record 33). It listens only on 127.0.0.1, at a port
    no other program uses, for the password it makes, and keeps its data in a folder of its own
    until it stops."""

    def __init__(self) -> None:
        self.bin = postgres_binaries()
        # Not in a folder from tempfile.mkdtemp: on Windows, Postgres drops its administrator's
        # rights as it starts, and can't then open a folder made for the administrator alone.
        self.folder = Path(tempfile.gettempdir(), f"sulba-postgres-{secrets.token_hex(8)}")
        self.folder.mkdir()
        self.port = free_port()
        self.password = secrets.token_urlsafe(16)
        self.databases = 0
        try:
            start_postgres(self.bin, self.folder / "data", self.port, self.password)
            self.sql("postgres", "CREATE DATABASE sulba_template")
            self.sql("sulba_template", "CREATE EXTENSION vector")
        except BaseException:
            self.stop()
            raise

    def url(self, database: str) -> str:
        return f"postgresql://postgres:{self.password}@127.0.0.1:{self.port}/{database}"

    def sql(self, database: str, command: str) -> None:
        run_postgres(
            [
                self.bin / executable("psql"),
                "--no-psqlrc",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                command,
                self.url(database),
            ]
        )

    def new_database(self) -> str:
        """The address of a new database, with pgvector installed."""
        self.databases += 1
        name = f"test_{self.databases}"
        self.sql("postgres", f"CREATE DATABASE {name} TEMPLATE sulba_template")
        return name

    def stop(self) -> None:
        data = self.folder / "data"
        if (data / "postmaster.pid").exists():
            run_postgres(
                [self.bin / executable("pg_ctl"), "stop", "-D", data, "-m", "immediate", "-w"],
                check=False,
            )
        shutil.rmtree(self.folder, ignore_errors=True)


def postgres_binaries() -> Path:
    """Where embedded-postgres keeps its Postgres 18 programs."""
    spec = importlib.util.find_spec("embedded_postgres")
    if spec is None or spec.origin is None:
        raise RuntimeError(
            "The database comes with embedded-postgres, which the lab's project lacks."
        )
    return Path(spec.origin).parent / "pginstall" / "bin"


def executable(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


def cache_folder() -> Path:
    """sulba in the cache folder, as Hugging Face's cache is placed: $XDG_CACHE_HOME where it's set,
    and ~/.cache otherwise, on every system."""
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "sulba"


def pgvector_folder() -> Path | None:
    """On Linux, the folder that holds the PostgreSQL project's pgvector for this machine, fetched
    into the cache folder the first time: its library in lib, and its control and script files in
    share/extension. Elsewhere None, for the pgvector that comes with embedded-postgres."""
    import platform

    if platform.system() != "Linux":
        return None
    machine = platform.machine()
    if machine not in PGVECTOR_BUILDS:
        raise RuntimeError(f"pgvector has no build for Linux on {machine}.")
    name, size, sha256 = PGVECTOR_BUILDS[machine]
    folder = cache_folder() / "pgvector" / sha256
    if (folder / "lib" / "vector.so").is_file():
        return folder
    package = fetched_package(f"{PGVECTOR_PACKAGES}/{name}", size, sha256, "pgvector")
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Unpacked beside its place first, so a run stopped halfway leaves no pgvector to find.
    unpacking = Path(tempfile.mkdtemp(dir=folder.parent))
    try:
        unpack_pgvector(package, unpacking)
        try:
            os.replace(unpacking, folder)
        except OSError:
            # Another run put it there first.
            if not (folder / "lib" / "vector.so").is_file():
                raise
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)
    return folder


def fetched_package(url: str, size: int, sha256: str, what: str) -> bytes:
    """The package at url, once it's the one its size and sha256 name. `what` names it in an
    error."""
    import hashlib
    import http.client
    import urllib.request
    from urllib.parse import urlsplit

    host = urlsplit(url).hostname
    request = urllib.request.Request(url, headers={"User-Agent": "sulba"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            package: bytes = response.read(size + 1)
    except (OSError, http.client.HTTPException) as error:
        raise RuntimeError(f"{what} comes from {host}, which didn't send it: {error}") from error
    if len(package) != size or hashlib.sha256(package).hexdigest() != sha256:
        raise RuntimeError(f"{host} sent a different {what} from the one the lab was made with.")
    return package


def unpack_pgvector(package: bytes, folder: Path) -> None:
    """Puts pgvector's library from a Debian package into folder/lib, and its control and script
    files into folder/share/extension, with the control file naming the library without a folder,
    so the server finds it in its dynamic_library_path."""
    import io
    import re
    import tarfile

    data = next(
        (contents for name, contents in ar_members(package) if name.startswith("data.tar")),
        None,
    )
    if data is None:
        raise RuntimeError("The pgvector package has no data.tar.")
    library = folder / "lib"
    extension = folder / "share" / "extension"
    library.mkdir(parents=True)
    extension.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as files:
        for member in files.getmembers():
            path = Path(member.name)
            if not member.isfile():
                continue
            if path.parent.name == "lib" and path.name == "vector.so":
                target = library / path.name
            elif path.parent.name == "extension" and path.name.startswith("vector"):
                target = extension / path.name
            else:
                continue
            source = files.extractfile(member)
            assert source is not None
            target.write_bytes(source.read())
    control = extension / "vector.control"
    if not (library / "vector.so").is_file() or not control.is_file():
        raise RuntimeError("The pgvector package lacks vector.so or vector.control.")
    text = control.read_text(encoding="utf-8")
    control.write_text(
        re.sub(r"(?m)^module_pathname = .*$", "module_pathname = 'vector'", text),
        encoding="utf-8",
    )


def ar_members(archive: bytes) -> Iterator[tuple[str, bytes]]:
    """Each file's name and contents in an ar archive, the format of a Debian package."""
    if not archive.startswith(b"!<arch>\n"):
        raise RuntimeError("The pgvector package isn't an ar archive.")
    offset = 8
    while offset + 60 <= len(archive):
        header = archive[offset : offset + 60]
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58].decode("ascii"))
        start = offset + 60
        yield name, archive[start : start + size]
        # Each file starts on an even byte.
        offset = start + size + size % 2


def check_system(*paths: Path) -> None:
    """Raises when Postgres can't run here: as root, which it refuses, or on Windows without AVX2,
    which pgvector's build there needs, or with a path the system's code page lacks a character
    of, since Postgres's programs take each path in that code page there."""
    if sys.platform != "win32":
        if os.geteuid() == 0:
            raise RuntimeError("Postgres doesn't run as root: run the lab as your own user.")
        return
    import ctypes
    import locale

    if not ctypes.windll.kernel32.IsProcessorFeaturePresent(PF_AVX2_INSTRUCTIONS_AVAILABLE):
        raise RuntimeError("pgvector's build for Windows needs a processor with AVX2.")
    encoding = locale.getencoding()
    for path in paths:
        try:
            str(path).encode(encoding)
        except UnicodeEncodeError:
            raise RuntimeError(
                f"Postgres can't use {path}: its name has a character that this computer's code "
                f"page, {encoding}, lacks. Move the lab to a folder whose name has none."
            ) from None


def free_port() -> int:
    """A TCP port on 127.0.0.1 that no program listens on now."""
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def run_postgres(command: list[Any], *, check: bool = True, output: Path | None = None) -> int:
    """Runs one of Postgres's programs, and gives its exit code, or raises with what it wrote
    if it fails and check is on. With output, what it writes goes to that file."""
    import subprocess

    arguments = [str(part) for part in command]
    environment = {**os.environ, "PGCLIENTENCODING": "UTF8"}
    if output is not None:
        with output.open("w", encoding="utf-8") as file:
            return subprocess.run(
                arguments, stdout=file, stderr=subprocess.STDOUT, env=environment
            ).returncode
    done = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )
    if check and done.returncode != 0:
        raise RuntimeError(
            f"{Path(command[0]).stem} failed: {(done.stderr or done.stdout).strip()}"
        )
    return done.returncode


def start_postgres(bin: Path, data: Path, port: int, password: str) -> None:
    """Starts a Postgres server on 127.0.0.1 at port, for the cluster in data, which it makes the
    first time: with the password for user postgres, and UTF-8 in the C.UTF-8 locale whatever
    the system's own."""
    import shlex

    check_system(bin, data)
    if not (data / "PG_VERSION").is_file():
        secret = data.with_name(f"{data.name}-password-file")
        secret.write_text(password, encoding="utf-8")
        try:
            run_postgres(
                [
                    bin / executable("initdb"),
                    "-D",
                    data,
                    "-U",
                    "postgres",
                    "--auth=scram-sha-256",
                    f"--pwfile={secret}",
                    "--encoding=UTF8",
                    "--locale=C",
                    "--locale-provider=builtin",
                    "--builtin-locale=C.UTF-8",
                    "--no-instructions",
                ]
            )
        finally:
            secret.unlink()
    options = f"-p {port} -c listen_addresses=127.0.0.1"
    if os.name != "nt":
        options += " -c unix_socket_directories="
    pgvector = pgvector_folder()
    if pgvector is not None:
        # pg_ctl starts the server through the shell, which would read $system and $libdir.
        for setting in (
            f"extension_control_path={pgvector / 'share'}:$system",
            f"dynamic_library_path={pgvector / 'lib'}:$libdir",
        ):
            options += f" -c {shlex.quote(setting)}"
    log = data.with_name(f"{data.name}.log")
    started = data.with_name(f"{data.name}-start.log")
    # pg_ctl's own output goes to a file too: the server it starts keeps whatever pg_ctl writes
    # to, and on Windows a pipe kept open would leave this waiting as long as the server runs.
    code = run_postgres(
        [
            bin / executable("pg_ctl"),
            "start",
            "-D",
            data,
            "-l",
            log,
            "-w",
            "-t",
            "60",
            "-o",
            options,
        ],
        check=False,
        output=started,
    )
    if code != 0:
        written = [
            path.read_text(encoding="utf-8", errors="replace")
            for path in (started, log)
            if path.exists()
        ]
        raise RuntimeError(f"pg_ctl failed: {chr(10).join(written)[-2000:]}")


@pytest.fixture(scope="session")
def postgres() -> Iterator[Postgres]:
    """The Postgres server for the run's tests, started when a test first asks for a database."""
    server = Postgres()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def database(postgres: Postgres) -> str:
    """The address of a new, empty Postgres database for the test, with pgvector installed, as a
    postgresql:// URL that psycopg connects to."""
    return postgres.url(postgres.new_database())


# Spark splits work into this many partitions, as Sail and as Spark's local[2], so a result that
# depends on how rows are split, such as a sum of floats, is the same on every machine.
SPARK_PARTITIONS = 2


@pytest.fixture(scope="session")
def spark_session() -> Iterator[Any]:
    """The run's Spark session, which its tests share: through Spark Connect to a Sail server in
    this process, or with SULBA_SPARK=jvm, Spark itself in local mode. Its time zone is UTC."""
    if SPARK == "jvm":
        from pyspark.sql import SparkSession

        session = (
            SparkSession.builder.master(f"local[{SPARK_PARTITIONS}]")
            .config("spark.ui.enabled", "false")
            .config("spark.sql.session.timeZone", "UTC")
            .getOrCreate()
        )
        try:
            yield session
        finally:
            session.stop()
        return
    if importlib.util.find_spec("pysail") is None:
        raise RuntimeError("Spark comes with pysail, which the lab's project lacks.")
    # Sail reads these as it starts: its partitions, and only its errors for the run's output.
    os.environ["SAIL_EXECUTION__DEFAULT_PARALLELISM"] = str(SPARK_PARTITIONS)
    os.environ.setdefault("RUST_LOG", "error")
    from pysail.spark import SparkConnectServer
    from pyspark.sql import SparkSession

    server = SparkConnectServer(ip="127.0.0.1", port=0)
    server.start()
    try:
        _, port = server.listening_address
        session = SparkSession.builder.remote(f"sc://127.0.0.1:{port}").getOrCreate()
        try:
            session.conf.set("spark.sql.session.timeZone", "UTC")
            yield session
        finally:
            # Before the server: a server stopped under an open session keeps the process alive.
            session.stop()
    finally:
        server.stop()


@pytest.fixture
def spark(spark_session: Any) -> Iterator[Any]:
    """A Spark session for the test, whose temporary views are dropped when it ends, so the next
    test starts with none."""
    yield spark_session
    for table in spark_session.catalog.listTables():
        if table.isTemporary:
            spark_session.catalog.dropTempView(table.name)
