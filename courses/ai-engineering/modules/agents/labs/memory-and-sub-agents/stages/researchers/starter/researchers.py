"""Researchers: a sub-agent for each service's help pages, which searches them in a context of
its own and gives the agent that asked only a short answer, with the passages it cites."""

import json
from collections.abc import Callable
from typing import Any

import httpx

from memory import MODEL, SAMPLING, Request

RESEARCHER = (
    "You research {name}'s help pages for a help desk's assistant, who asks you one question at "
    "a time. Search the pages, then answer in at most 100 words from what you found, citing "
    "each passage you use by its id in square brackets, like [p17]. If the pages don't answer, "
    "say so."
)
# The desk's system prompt's line on questions, for research in place of search_help.
ASK = (
    "- Answer questions about the services from their help pages: ask the service's researcher, "
    "and cite each passage its answer cites by its id in square brackets, like [p17]. If it "
    "finds no answer, say so.\n"
)
SEARCH = {
    "type": "function",
    "function": {
        "name": "search_pages",
        "description": "Search the help pages. Gives the 5 best passages, each led by its id.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for."}
            },
            "required": ["query"],
        },
    },
}


class Researcher:
    """The researcher of one service's help pages: search, given a query and the service, gives
    the passages it finds as text. Each question gets a conversation of its own, of at most
    rounds requests, the last of them without tools so that the model answers."""

    def __init__(
        self,
        client: httpx.Client,
        search: Callable[[str, str], str],
        service: str,
        name: str,
        rounds: int = 3,
        max_tokens: int = 300,
    ) -> None:
        self.client = client
        self.search = search
        self.service = service
        self.system = RESEARCHER.format(name=name)
        self.rounds = rounds
        self.max_tokens = max_tokens
        self.requests: list[Request] = []

    def run(self, arguments: str) -> str:
        try:
            given = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            given = None
        if not isinstance(given, dict) or not isinstance(given.get("query"), str):
            return 'Error: search_pages takes one query, like {"query": "replace a lost card"}'
        return self.search(given["query"], self.service)

    def answer(self, question: str) -> str:
        raise NotImplementedError


class Researchers:
    """A researcher for each service, which research asks by the service's id."""

    def __init__(
        self,
        client: httpx.Client,
        search: Callable[[str, str], str],
        services: dict[str, str],
        **options: Any,
    ) -> None:
        self.researchers = {
            service: Researcher(client, search, service, name, **options)
            for service, name in services.items()
        }

    def research(self, service: str, question: str) -> str:
        raise NotImplementedError

    def tool(self) -> dict[str, Any]:
        """research, as a chat request's tools give it."""
        return {
            "type": "function",
            "function": {
                "name": "research",
                "description": "Ask the researcher of one service's help pages a question. "
                "Gives its short answer, with the ids of the passages it cites, which you cite "
                "as it does.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "enum": list(self.researchers)},
                        "question": {
                            "type": "string",
                            "description": "The caller's question, in full.",
                        },
                    },
                    "required": ["service", "question"],
                },
            },
        }

    def call(self, name: str, arguments: str) -> str:
        """Runs a call of research, by its arguments as JSON text."""
        raise NotImplementedError
