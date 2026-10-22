"""The desk's replies, by the assistant: the caller's message in, the reply out as server-sent
events through the gate."""

from collections.abc import AsyncIterable, Callable
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, StringConstraints
from starlette.exceptions import HTTPException

from agent import Agent, Done, ModelError, OutOfRounds, Text, Tool
from conversations import Conversation, Conversations, Message, Page
from gate import Busy, Gate, within


class Say(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


class Agents:
    """An agent for each conversation, and the conversations being replied in."""

    def __init__(self, make: Callable[[Page | None], Agent]) -> None:
        self.make = make
        self.held: dict[str, Agent] = {}
        self.replying: set[str] = set()

    def of(self, conversation: Conversation) -> Agent:
        if conversation.id not in self.held:
            self.held[conversation.id] = self.make(conversation.page)
        return self.held[conversation.id]


async def turn(
    conversation_id: str, say: Say, request: Request
) -> tuple[Conversation, str]:
    conversations: Conversations = request.app.state.conversations
    agents: Agents = request.app.state.agents
    gate: Gate = request.app.state.gate
    try:
        await gate.enter()
    except Busy as busy:
        raise HTTPException(
            503,
            "The desk is answering as many callers as it can.",
            {"Retry-After": str(busy.retry_after)},
        ) from None
    conversation = conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(404, "There's no conversation with this id.")
    if conversation.id in agents.replying:
        raise HTTPException(409, "The desk is still replying in this conversation.")
    agents.replying.add(conversation.id)
    return conversation, say.content


router = APIRouter()


@router.post(
    "/conversations/{conversation_id}/messages", response_class=EventSourceResponse
)
async def say(
    request: Request, turn: tuple[Conversation, str] = Depends(turn)
) -> AsyncIterable[ServerSentEvent]:
    conversations: Conversations = request.app.state.conversations
    agents: Agents = request.app.state.agents
    gate: Gate = request.app.state.gate
    conversation, content = turn
    agent = agents.make(conversation.page)
    before = len(agent.messages)
    kept = False
    try:
        async for event in agent.reply(content):
            if isinstance(event, Text):
                yield ServerSentEvent(event="text", data={"delta": event.delta})
            elif isinstance(event, Tool):
                yield ServerSentEvent(event="tool", data={"name": event.name})
            elif isinstance(event, Done):
                conversations.add(
                    conversation.id, Message(role="caller", content=content)
                )
                conversations.add(
                    conversation.id, Message(role="desk", content=event.text)
                )
                kept = True
                gate.leave()
                yield ServerSentEvent(event="done", data={"content": event.text})
    except TimeoutError:
        yield ServerSentEvent(event="error", data={"title": "The reply took too long."})
    except ModelError, OutOfRounds, httpx.HTTPError:
        yield ServerSentEvent(event="error", data={"title": "The desk couldn't reply."})
    finally:
        if not kept:
            del agent.messages[before:]
        agents.replying.discard(conversation.id)
