"""The desk's replies: the caller's message in, and the desk's reply out as server-sent events,
each piece as it comes, through the gate in front of the model. Every turn is kept in the
database with what it used, however it ends, and its messages once it's done."""

import asyncio
from collections.abc import AsyncIterable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

import anyio
import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, StringConstraints
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from agent import Agent, Done, ModelError, OutOfRounds, Text, Tool
from conversations import Conversation, Message, Page
from gate import Busy, Gate, within
from sessions import Account, signed_in
from store import Outcome, Store, Usage


class Say(BaseModel):
    """The caller's message: from 1 to 2,000 characters, without the spaces at its ends."""

    model_config = ConfigDict(extra="forbid")

    content: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]


class Agents:
    """Each conversation's agent, which make gives it for its help pages the first time this
    run of the app replies in it, and the conversations a reply is running for."""

    def __init__(self, make: Callable[[Page | None], Agent]) -> None:
        self.make = make
        self.held: dict[str, Agent] = {}
        self.replying: set[str] = set()

    def of(self, conversation: Conversation) -> Agent:
        if conversation.id not in self.held:
            agent = self.make(conversation.page)
            # A conversation kept by an earlier run of the app goes on from its messages.
            agent.messages += [
                {
                    "role": "user" if message.role == "caller" else "assistant",
                    "content": message.content,
                }
                for message in conversation.messages
            ]
            self.held[conversation.id] = agent
        return self.held[conversation.id]


@dataclass(frozen=True)
class Turn:
    """A message the desk is to reply to, in its conversation, with a place at the gate."""

    conversation: Conversation
    content: str


def found(
    conversation_id: str, request: Request, person: Account = Depends(signed_in)
) -> Conversation:
    """The person's conversation, from the database, or a 404."""
    store: Store = request.app.state.conversations
    conversation = store.get(conversation_id, person.id)
    if conversation is None:
        raise HTTPException(404, "There's no conversation with this id.")
    return conversation


async def turn(
    say: Say, request: Request, conversation: Conversation = Depends(found)
) -> Turn:
    """The turn, once the message fits and its conversation is there: one reply at a time in a
    conversation, and a place at the gate for it."""
    agents: Agents = request.app.state.agents
    gate: Gate = request.app.state.gate
    if conversation.id in agents.replying:
        raise HTTPException(409, "The desk is still replying in this conversation.")
    agents.replying.add(conversation.id)
    try:
        await gate.enter()
    except BaseException as error:
        # Turned away, or gone while waiting: the conversation takes a message again.
        agents.replying.discard(conversation.id)
        if isinstance(error, Busy):
            raise HTTPException(
                503,
                "The desk is answering as many callers as it can.",
                {"Retry-After": str(error.retry_after)},
            ) from None
        raise
    return Turn(conversation, say.content)


router = APIRouter()


@router.post(
    "/conversations/{conversation_id}/messages", response_class=EventSourceResponse
)
async def say(
    request: Request, turn: Turn = Depends(turn)
) -> AsyncIterable[ServerSentEvent]:
    """The desk's reply as it comes: a text event with each piece, a tool event for each tool it
    runs, and a done event with the whole reply, once the turn is kept; or an error event. The
    database work runs in the threadpool, off the event loop."""
    agents: Agents = request.app.state.agents
    store: Store = request.app.state.conversations
    gate: Gate = request.app.state.gate
    conversation = turn.conversation
    agent = agents.of(conversation)
    before = len(agent.messages)
    loop = asyncio.get_running_loop()
    started_at, began = datetime.now(UTC), loop.time()
    # Until the reply ends some other way, the caller has left.
    outcome: Outcome = "left"

    def used(outcome: Outcome) -> Usage:
        seconds = loop.time() - began
        return Usage(
            started_at, seconds, agent.prompt_tokens, agent.completion_tokens, outcome
        )

    try:
        async for event in within(agent.reply(turn.content), gate.seconds):
            match event:
                case Text(delta):
                    yield ServerSentEvent(event="text", data={"delta": delta})
                case Tool(name):
                    yield ServerSentEvent(event="tool", data={"name": name})
                case Done(text):
                    said = [
                        Message(role="caller", content=turn.content),
                        Message(role="desk", content=text),
                    ]
                    await run_in_threadpool(
                        store.keep, conversation.id, used("done"), said
                    )
                    outcome = "done"
                    yield ServerSentEvent(event="done", data={"content": text})
    except TimeoutError:
        outcome = "too long"
        yield ServerSentEvent(event="error", data={"title": "The reply took too long."})
    except ModelError, OutOfRounds, httpx.HTTPError:
        outcome = "failed"
        yield ServerSentEvent(event="error", data={"title": "The desk couldn't reply."})
    finally:
        try:
            if outcome != "done":
                del agent.messages[before:]
                # A caller who leaves cancels the reply's work, and the shield lets the
                # turn be kept all the same.
                with anyio.CancelScope(shield=True):
                    await run_in_threadpool(store.keep, conversation.id, used(outcome))
        finally:
            agents.replying.discard(conversation.id)
            gate.leave()
