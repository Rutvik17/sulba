"""The service's lookups for a day's codes: at a limit, in time, and with a lookup that
fails kept to its own code."""

import asyncio


class Registry:
    """A stand-in for the clinic's registry. It knows some codes and answers each lookup
    after latency seconds, or after slow[code] for a code in slow. It keeps each code it's
    asked about, and counts the lookups it serves at once."""

    def __init__(self, known, latency=0.25, slow=None, failing=()):
        self.known = set(known)
        self.latency = latency
        self.slow = dict(slow or {})
        self.failing = set(failing)
        self.asked = []
        self.serving = 0
        self.most = 0

    async def lookup(self, code):
        """Whether the registry knows code. A lookup of a code in failing raises
        ConnectionError."""
        self.asked.append(code)
        self.serving += 1
        self.most = max(self.most, self.serving)
        try:
            await asyncio.sleep(self.slow.get(code, self.latency))
            if code in self.failing:
                raise ConnectionError(f"The registry dropped the lookup of {code!r}")
            return code in self.known
        finally:
            self.serving -= 1


def answer(code, known):
    """None for a known code, or the message for an unknown one."""
    return None if known else f"No patient has the code {code!r}"


async def check_code(code, registry):
    """None when the registry knows code, or the message for an unknown one."""
    if await registry.lookup(code):
        return None
    return f"No patient has the code {code!r}"


async def check_limited(codes, registry, limit):
    """Each code's check, with no more than limit lookups at a time, and a message for a
    lookup that couldn't reach the registry."""
    gate = asyncio.Semaphore(limit)

    async def limited(code):
        async with gate:
            known = await registry.lookup(code)
        return answer(code, known)

    results = await asyncio.gather(
        *(limited(code) for code in codes), return_exceptions=True
    )
    return [
        f"The registry couldn't be reached for {code!r}"
        if isinstance(result, ConnectionError)
        else result
        for code, result in zip(codes, results, strict=True)
    ]


async def check_each(codes, registry):
    """Each code's check, with every lookup at once, and a message for a lookup that
    couldn't reach the registry."""

    async def one(code):
        try:
            return answer(code, await registry.lookup(code))
        except ConnectionError:
            return f"The registry couldn't be reached for {code!r}"

    return await asyncio.gather(*(one(code) for code in codes))


async def check_in_time(codes, registry, seconds):
    """Each code's check, with every lookup at once, and a message for a lookup that takes
    longer than seconds."""

    async def one(code):
        try:
            async with asyncio.timeout(seconds):
                return answer(code, await registry.lookup(code))
        except TimeoutError:
            return f"The registry took too long for {code!r}"

    return await asyncio.gather(*(one(code) for code in codes))
