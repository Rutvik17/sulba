"""The shop's tools, served over the Model Context Protocol, version 2026-07-28: each line that
comes in is one JSON-RPC message, and each reply one line out, as MCP's stdio transport carries
them."""

import io
import sys
from collections.abc import Callable, Iterable
from typing import Any, TextIO

from assistant import opening_hours, repair_price

VERSION = "2026-07-28"
SERVER = {"name": "bike-shop", "version": "1.0.0"}
# How long a client may keep the server's discovery and tools before asking again, in
# milliseconds.
TTL = 3_600_000


class Server:
    """An MCP server for the shop's functions, each one a tool."""

    def __init__(self, functions: list[Callable[..., Any]]) -> None:
        self.functions = {function.__name__: function for function in functions}

    def handle(self, line: str) -> str | None:
        """The reply to one message, as a line of JSON, or None for a notification."""
        raise NotImplementedError


def serve(server: Server, lines: Iterable[str], out: TextIO) -> None:
    """Answers each message in lines, writing each reply to out on a line of its own."""
    raise NotImplementedError


if __name__ == "__main__":
    # MCP's messages are UTF-8, whatever the system's own encoding.
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
    serve(Server([opening_hours, repair_price]), lines, out)
