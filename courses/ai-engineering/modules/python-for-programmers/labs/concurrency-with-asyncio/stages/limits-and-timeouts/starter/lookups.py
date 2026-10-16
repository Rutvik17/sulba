async def check_limited(codes, registry, limit):
    """Each code's check, in order, with no more than limit lookups at a time."""
    raise NotImplementedError


async def check_in_time(code, registry, seconds):
    """The code's check, or "The registry took too long for 'S00003'" when its lookup
    takes longer than seconds."""
    raise NotImplementedError
