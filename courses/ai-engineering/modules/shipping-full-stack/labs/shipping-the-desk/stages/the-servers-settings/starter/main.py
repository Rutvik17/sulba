"""The desk as a host runs it: its logs as JSON lines with each request's id, its readiness at
/ready, and the server's settings from the environment the host gives it.

    uv run main.py
"""

import os
from collections.abc import Mapping

import serve
import uvicorn
from fastapi import FastAPI
from logs import configure

# Seconds the server gives open requests once it's told to stop, under the 30 a host such as
# Render waits before it ends the process.
SHUTDOWN_SECONDS = 25

# The proxies trusted to say who the caller is when FORWARDED_ALLOW_IPS names none: the
# machine itself.
LOOPBACK = "127.0.0.1,::1"


def production(app: FastAPI) -> FastAPI:
    """The app with its readiness at /ready and an id for each request in its logs."""
    raise NotImplementedError


def create() -> FastAPI:
    """The desk with its page, its logs sent to standard output as JSON."""
    configure()
    return production(serve.create())


def port_from(environ: Mapping[str, str]) -> int:
    """The port in PORT, or 8000 if it isn't set."""
    raise NotImplementedError


def config(environ: Mapping[str, str]) -> uvicorn.Config:
    """The server's settings: every address of the machine, on the port in PORT; a caller's
    address from forwarded headers only when the proxies FORWARDED_ALLOW_IPS names send them;
    SHUTDOWN_SECONDS for open requests once it's told to stop; and the desk's logs, not
    uvicorn's own."""
    raise NotImplementedError


if __name__ == "__main__":
    uvicorn.Server(config(os.environ)).run()
