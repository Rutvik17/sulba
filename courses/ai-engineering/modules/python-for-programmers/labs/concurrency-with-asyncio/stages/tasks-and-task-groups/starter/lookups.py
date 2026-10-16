async def check_at_once(codes, registry):
    """Each code's check, in order, with every lookup made at once."""
    raise NotImplementedError


async def check_all(codes, registry):
    """Each code's check, in order, with every lookup made at once in a task group. When
    lookups fail, an ExceptionGroup of their errors, with the lookups still waiting
    cancelled."""
    raise NotImplementedError


async def check_each(codes, registry):
    """Each code's check, in order, with every lookup made at once, and "The registry
    couldn't be reached for 'S00003'" for a lookup that raised ConnectionError."""
    raise NotImplementedError
