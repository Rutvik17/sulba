async def check_day(codes, registry, limit, seconds):
    """Each code's check, in order, with no more than limit lookups at a time, each lookup
    given seconds from when it starts, and a message for a lookup that couldn't reach the
    registry or took too long. Any other error ends the day, with no lookup left running."""
    raise NotImplementedError
