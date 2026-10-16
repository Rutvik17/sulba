"""The service's lookups in the clinic's registry of patients."""

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


async def check_code(code, registry):
    """None when the registry knows code, or "No patient has the code 'S00003'"."""
    if await registry.lookup(code):
        return None
    return f"No patient has the code {code!r}"


async def check_codes(codes, registry):
    """Each code's check, in order, one lookup after another."""
    return [await check_code(code, registry) for code in codes]


async def first_unknown(codes, registry):
    """The first code the registry doesn't know, or None, asking about no code after it."""
    for code in codes:
        if not await registry.lookup(code):
            return code
    return None


async def check_at_once(codes, registry):
    """Each code's check, in order, with every lookup made at once."""
    return await asyncio.gather(*(check_code(code, registry) for code in codes))


async def check_all(codes, registry):
    """Each code's check, in order, with every lookup made at once in a task group. When
    lookups fail, an ExceptionGroup of their errors, with the lookups still waiting
    cancelled."""
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(check_code(code, registry)) for code in codes]
    return [task.result() for task in tasks]


async def check_each(codes, registry):
    """Each code's check, in order, with every lookup made at once, and "The registry
    couldn't be reached for 'S00003'" for a lookup that raised ConnectionError."""
    results = await asyncio.gather(
        *(check_code(code, registry) for code in codes), return_exceptions=True
    )
    checks = []
    for code, result in zip(codes, results, strict=True):
        if isinstance(result, ConnectionError):
            checks.append(f"The registry couldn't be reached for {code!r}")
        elif isinstance(result, BaseException):
            raise result
        else:
            checks.append(result)
    return checks
