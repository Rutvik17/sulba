"""The loop fixture your tests ask for, as the lab gives it."""

import asyncio

import pytest


@pytest.fixture
def loop():
    """A new event loop for the test, closed after it."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()
