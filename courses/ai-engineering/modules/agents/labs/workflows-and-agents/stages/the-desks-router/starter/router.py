"""The desk as a router: the model sorts the caller's first message, and a route the workflow
can follow goes down its path, while any other goes to the agent, which keeps the conversation
from there."""

import httpx

from agent import Agent
from desk import Desk
from workflow import Route, Workflow, route


class Router:
    """One conversation with the caller, through the desk, from the help pages the chat was
    opened from, or None for the desk's home page."""

    def __init__(self, client: httpx.Client, desk: Desk, page: str | None) -> None:
        self.client = client
        self.desk = desk
        self.page = page
        self.chosen: Workflow | Agent | None = None

    def follows(self, found: Route) -> bool:
        """Whether the workflow follows the route."""
        raise NotImplementedError

    def reply(self, message: str) -> str:
        """The desk's reply to the caller's next message."""
        raise NotImplementedError
