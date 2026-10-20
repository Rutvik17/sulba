"""The fixtures a session's tests can ask for: `loop`, an event loop on a virtual clock (decision
record 21), `typecheck`, mypy's errors in the session's files (decision record 22), `model`, a
model server that answers with the replies the test scripts (decision record 31), and on the
learner's machine `database`, a new Postgres database with pgvector (decision record 33).

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
import os
import secrets
import shutil
import sys
import tempfile
from collections import deque
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
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
    import importlib.util

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
    package = fetched_package(f"{PGVECTOR_PACKAGES}/{name}", size, sha256)
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


def fetched_package(url: str, size: int, sha256: str) -> bytes:
    """The package at url, once it's the one its size and sha256 name."""
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
        raise RuntimeError(
            f"pgvector for Linux comes from {host}, which didn't send it: {error}"
        ) from error
    if len(package) != size or hashlib.sha256(package).hexdigest() != sha256:
        raise RuntimeError(f"{host} sent a different pgvector from the one the lab was made with.")
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
