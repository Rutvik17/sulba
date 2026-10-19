import io
import json
from typing import Annotated, Literal

import pytest

from server import TTL, Server, serve
from tools import describe

VERSION = "2026-07-28"
META = {
    "io.modelcontextprotocol/protocolVersion": VERSION,
    "io.modelcontextprotocol/clientCapabilities": {},
}
Day = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
Service = Literal["puncture", "brakes", "gears", "full service"]


def opening_hours(day: Day) -> str:
    """The shop's opening hours on a day of the week."""
    return {"Saturday": "9:00 to 13:00", "Sunday": "Closed"}.get(day, "9:00 to 17:00")


def repair_price(service: Service, bikes: Annotated[int, "How many bikes"]) -> float:
    """The price of a repair, in pounds."""
    if bikes < 1:
        raise ValueError("A repair is for one bike or more.")
    return {"puncture": 12.0, "brakes": 18.0, "gears": 25.0, "full service": 60.0}[
        service
    ] * bikes


def shop():
    return Server([opening_hours, repair_price])


def request(id, method, meta=META, **params):
    return {
        "jsonrpc": "2.0",
        "id": id,
        "method": method,
        "params": {**params, "_meta": meta},
    }


def send(server, message):
    line = message if isinstance(message, str) else json.dumps(message)
    answered = server.handle(line)
    assert answered is not None and "\n" not in answered and "\r" not in answered
    return json.loads(answered)


def error(found, code):
    assert found["jsonrpc"] == "2.0" and "result" not in found, found
    assert found["error"]["code"] == code and isinstance(found["error"]["message"], str)
    return found


@pytest.mark.id("tst_75811q")
def test_replies():
    """Answers each request on one line, with its id, and through serve"""
    server = shop()
    for id in [7, "call-7", 0]:
        found = send(server, request(id, "tools/list"))
        assert (
            found["jsonrpc"] == "2.0" and found["id"] == id and found["id"] is not True
        )
        assert found["result"]["resultType"] == "complete"
    out = io.StringIO()
    lines = [
        json.dumps(request(1, "server/discover")),
        json.dumps(request(2, "tools/list")),
    ]
    serve(server, lines, out)
    replies = out.getvalue().splitlines()
    assert [json.loads(line)["id"] for line in replies] == [1, 2]
    assert out.getvalue().endswith("\n")


@pytest.mark.id("tst_dkcqjc")
def test_notifications():
    """Never answers a notification, whatever its method"""
    server = shop()
    for method in ["notifications/cancelled", "tools/call", "no/such/method"]:
        message = {"jsonrpc": "2.0", "method": method, "params": {"_meta": META}}
        assert server.handle(json.dumps(message)) is None
    out = io.StringIO()
    serve(
        server,
        [json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled"})],
        out,
    )
    assert out.getvalue() == ""


@pytest.mark.id("tst_ljim9t")
def test_not_json_rpc():
    """Refuses what isn't JSON-RPC, with the request's id when it can be read"""
    server = shop()
    found = error(
        send(server, '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"'), -32700
    )
    assert "id" not in found
    found = error(send(server, json.dumps([request(1, "tools/list")])), -32600)
    assert "id" not in found
    found = error(send(server, {**request(2, "tools/list"), "jsonrpc": "1.0"}), -32600)
    assert found["id"] == 2
    found = error(
        send(server, {"jsonrpc": "2.0", "id": 3, "params": {"_meta": META}}), -32600
    )
    assert found["id"] == 3
    found = error(
        send(server, {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": []}),
        -32600,
    )
    assert found["id"] == 4
    for id in [None, 1.5, True, {"n": 1}]:
        found = error(send(server, request(id, "tools/list")), -32600)
        assert "id" not in found


@pytest.mark.id("tst_6c2zay")
def test_protocol_version():
    """Reads each request's protocol version and capabilities from its _meta"""
    server = shop()
    for meta in [
        {},
        {"io.modelcontextprotocol/protocolVersion": VERSION},
        {"io.modelcontextprotocol/clientCapabilities": {}},
    ]:
        error(send(server, request(5, "tools/list", meta=meta)), -32602)
    error(send(server, {"jsonrpc": "2.0", "id": 5, "method": "tools/list"}), -32602)
    older = {**META, "io.modelcontextprotocol/protocolVersion": "2025-11-25"}
    found = error(send(server, request(6, "tools/list", meta=older)), -32022)
    assert found["id"] == 6
    assert found["error"]["data"] == {"supported": [VERSION], "requested": "2025-11-25"}


@pytest.mark.id("tst_qjrvcs")
def test_lists_tools():
    """Lists the shop's tools, each with its input schema"""
    server = shop()
    found = send(server, request(1, "tools/list"))["result"]
    assert found["tools"] == [
        {
            "name": each["function"]["name"],
            "description": each["function"]["description"],
            "inputSchema": each["function"]["parameters"],
        }
        for each in [describe(opening_hours), describe(repair_price)]
    ]
    assert found["_meta"]["io.modelcontextprotocol/serverInfo"]["name"]
    assert found["ttlMs"] == TTL and found["cacheScope"] == "public"
    found = send(server, request(2, "server/discover"))["result"]
    assert found["supportedVersions"] == [VERSION] and "tools" in found["capabilities"]
    assert found["ttlMs"] == TTL and found["cacheScope"] == "public"
    error(send(server, request(3, "prompts/list")), -32601)


@pytest.mark.id("tst_tfg2pb")
def test_calls_tools():
    """Calls a tool, and reports its errors where the model can read them"""
    server = shop()

    def call(name, arguments):
        return send(server, request(9, "tools/call", name=name, arguments=arguments))

    found = call("repair_price", {"service": "brakes", "bikes": 2})["result"]
    assert found == {**found, "resultType": "complete", "isError": False}
    assert found["content"] == [{"type": "text", "text": "36.0"}]
    for name, arguments in [
        ("repair_price", {"service": "brakes"}),
        ("repair_price", {"service": "brakes", "bikes": "two"}),
        ("repair_price", {"service": "brakes", "bikes": 2.5}),
        ("repair_price", {"service": "brakes", "bikes": True}),
        ("repair_price", {"service": "bmx", "bikes": 1}),
        ("repair_price", {"service": "brakes", "bikes": 1, "price": 0}),
        ("opening_hours", {"day": "Funday"}),
        ("opening_hours", {}),
    ]:
        found = call(name, arguments)["result"]
        assert found["isError"] is True and found["content"][0]["type"] == "text", (
            arguments
        )
    found = call("repair_price", {"service": "brakes", "bikes": 0})["result"]
    assert found["isError"] is True
    assert found["content"] == [
        {"type": "text", "text": "A repair is for one bike or more."}
    ]
    error(call("refund", {"booking": "B-1042"}), -32602)
    error(call("repair_price", "brakes"), -32602)
    error(send(server, request(10, "tools/call", arguments={})), -32602)
