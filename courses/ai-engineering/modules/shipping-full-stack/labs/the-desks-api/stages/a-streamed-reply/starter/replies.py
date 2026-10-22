"""The desk's replies: the caller's message in, and the desk's reply out as server-sent events,
each piece as it comes, through the gate in front of the model."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from agent import Agent
from conversations import Conversation, Conversations, Page, held


class Say(BaseModel):
    """The caller's message: from 1 to 2,000 characters, without the spaces at its ends."""

    content: str


class Agents:
    """Each conversation's agent, which make gives it for its help pages on its first message,
    and the conversations a reply is running for."""

    def __init__(self, make: Callable[[Page | None], Agent]) -> None:
        self.make = make
        self.held: dict[str, Agent] = {}
        self.replying: set[str] = set()

    def of(self, conversation: Conversation) -> Agent:
        raise NotImplementedError


@dataclass(frozen=True)
class Turn:
    """A message the desk is to reply to, in its conversation, with a place at the gate."""

    conversation: Conversation
    content: str


def found(
    conversation_id: str, conversations: Conversations = Depends(held)
) -> Conversation:
    raise NotImplementedError


async def turn(
    say: Say, request: Request, conversation: Conversation = Depends(found)
) -> Turn:
    """The turn, once the message fits and its conversation is there: one reply at a time in a
    conversation, and a place at the gate for it."""
    raise NotImplementedError


router = APIRouter()
