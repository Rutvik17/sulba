"""The shop's tools, served over the Model Context Protocol, version 2026-07-28: each line that
comes in is one JSON-RPC message, and each reply one line out, as MCP's stdio transport carries
them."""

import io
import json
import sys
from collections.abc import Callable, Iterable
from typing import Any, TextIO

from jsonschema import Draft202012Validator

from assistant import opening_hours, repair_price
from tools import describe

VERSION = "2026-07-28"
SERVER = {"name": "bike-shop", "version": "1.0.0"}
# How long a client may keep the server's discovery and tools before asking again, in
# milliseconds.
TTL = 3_600_000
PROTOCOL = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
SERVER_INFO = "io.modelcontextprotocol/serverInfo"


class Failed(Exception):
    """A request the server answers with a JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            self.error["data"] = data


class Server:
    """An MCP server for the shop's functions, each one a tool."""

    def __init__(self, functions: list[Callable[..., Any]]) -> None:
        self.functions = {function.__name__: function for function in functions}
        self.tools = []
        for function in functions:
            described = describe(function)["function"]
            self.tools.append(
                {
                    "name": described["name"],
                    "description": described["description"],
                    "inputSchema": described["parameters"],
                }
            )

    def handle(self, line: str) -> str | None:
        """The reply to one message, as a line of JSON, or None for a notification."""
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            return reply({"error": {"code": -32700, "message": "Parse error"}})
        if not isinstance(message, dict):
            return reply({"error": {"code": -32600, "message": "Invalid Request"}})
        known = "id" in message and is_id(message["id"])
        sent = {"id": message["id"]} if known else {}
        if (
            ("id" in message and not known)
            or message.get("jsonrpc") != "2.0"
            or not isinstance(message.get("method"), str)
            or not isinstance(message.get("params", {}), dict)
        ):
            return reply(
                {**sent, "error": {"code": -32600, "message": "Invalid Request"}}
            )
        if not known:
            return None
        try:
            result = self.answer(message["method"], message.get("params", {}))
        except Failed as failed:
            return reply({**sent, "error": failed.error})
        result = {"resultType": "complete", **result, "_meta": {SERVER_INFO: SERVER}}
        return reply({**sent, "result": result})

    def answer(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """The result of a request, or Failed with its error."""
        meta = params.get("_meta")
        if (
            not isinstance(meta, dict)
            or not isinstance(meta.get(PROTOCOL), str)
            or not isinstance(meta.get(CAPABILITIES), dict)
        ):
            raise Failed(
                -32602, f"Every request needs {PROTOCOL} and {CAPABILITIES} in _meta"
            )
        if meta[PROTOCOL] != VERSION:
            data = {"supported": [VERSION], "requested": meta[PROTOCOL]}
            raise Failed(-32022, "Unsupported protocol version", data)
        if method == "server/discover":
            return {
                "supportedVersions": [VERSION],
                "capabilities": {"tools": {}},
                "ttlMs": TTL,
                "cacheScope": "public",
            }
        if method == "tools/list":
            return {"tools": self.tools, "ttlMs": TTL, "cacheScope": "public"}
        if method == "tools/call":
            return self.call(params)
        raise Failed(-32601, f"Method not found: {method}")

    def call(self, params: dict[str, Any]) -> dict[str, Any]:
        """A tool call's result: what the tool returns, or what went wrong, for the model."""
        name, arguments = params.get("name"), params.get("arguments", {})
        if not isinstance(name, str) or not isinstance(arguments, dict):
            raise Failed(
                -32602, "A call needs a tool's name and an object of arguments"
            )
        if name not in self.functions:
            raise Failed(-32602, f"Unknown tool: {name}")
        schema = next(
            tool["inputSchema"] for tool in self.tools if tool["name"] == name
        )
        problems = [
            error.message
            for error in Draft202012Validator(schema).iter_errors(arguments)
        ]
        if problems:
            return failure(f"Invalid arguments for tool {name}: {'; '.join(problems)}")
        try:
            value = self.functions[name](**arguments)
        except Exception as error:
            return failure(str(error))
        text = json.dumps(value, ensure_ascii=False)
        return {"content": [{"type": "text", "text": text}], "isError": False}


def is_id(value: Any) -> bool:
    """Whether a request's id is one MCP allows: a string or an integer."""
    return isinstance(value, str) or (
        isinstance(value, int) and not isinstance(value, bool)
    )


def failure(text: str) -> dict[str, Any]:
    """A tool's result that tells the model what went wrong."""
    return {"content": [{"type": "text", "text": text}], "isError": True}


def reply(fields: dict[str, Any]) -> str:
    """A JSON-RPC response, on one line."""
    return json.dumps({"jsonrpc": "2.0", **fields}, ensure_ascii=False)


def serve(server: Server, lines: Iterable[str], out: TextIO) -> None:
    """Answers each message in lines, writing each reply to out on a line of its own."""
    for line in lines:
        answered = server.handle(line)
        if answered is not None:
            out.write(answered + "\n")
            out.flush()


if __name__ == "__main__":
    # MCP's messages are UTF-8, whatever the system's own encoding.
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
    serve(Server([opening_hours, repair_price]), lines, out)
