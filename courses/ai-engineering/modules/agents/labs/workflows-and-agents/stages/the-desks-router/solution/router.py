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
        """Whether the workflow follows the route: a question, a case for a service, or a
        callback for a service on a day, with at most one open ticket for that service."""
        if found.kind == "question":
            return True
        if found.kind == "case":
            return found.service is not None
        if found.kind != "callback" or found.service is None or found.day is None:
            return False
        tickets = [
            ticket
            for ticket in self.desk.tickets
            if ticket["service"] == found.service and ticket["status"] == "open"
        ]
        return len(tickets) <= 1

    def reply(self, message: str) -> str:
        """The desk's reply to the caller's next message."""
        if self.chosen is not None:
            return self.chosen.reply(message)
        found = route(self.client, message, self.page)
        if self.follows(found):
            workflow = Workflow(self.client, self.desk, self.page)
            self.chosen = workflow
            return workflow.reply(message, found)
        self.chosen = Agent(self.client, self.desk, self.page)
        return self.chosen.reply(message)
