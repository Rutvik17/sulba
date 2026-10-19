import json
from typing import Literal

import pytest

from server import Server

META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}
Day = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


def opening_hours(day: Day) -> str:
    """The shop's opening hours on a day of the week."""
    return {"Saturday": "9:00 to 13:00", "Sunday": "Closed"}.get(day, "9:00 to 17:00")


def send(server, id, method, **params):
    line = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": id,
            "method": method,
            "params": {**params, "_meta": META},
        }
    )
    return json.loads(server.handle(line))


@pytest.mark.id("tst_wlm8d4")
def test_discover():
    """server/discover gives the version and the tools capability"""
    found = send(Server([opening_hours]), 1, "server/discover")
    assert found["jsonrpc"] == "2.0" and found["id"] == 1
    assert found["result"]["resultType"] == "complete"
    assert found["result"]["supportedVersions"] == ["2026-07-28"]
    assert "tools" in found["result"]["capabilities"]


@pytest.mark.id("tst_w6uchs")
def test_call():
    """A tool's call gives its result as text"""
    found = send(
        Server([opening_hours]),
        "a",
        "tools/call",
        name="opening_hours",
        arguments={"day": "Saturday"},
    )
    assert found["id"] == "a"
    assert found["result"]["content"] == [
        {"type": "text", "text": json.dumps("9:00 to 13:00")}
    ]
    assert found["result"]["isError"] is False
