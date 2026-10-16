def days_until_warmer(temperatures):
    """For each day, how many days until a warmer one, or 0 if none comes."""
    waits = [0] * len(temperatures)
    waiting = []
    for day, temperature in enumerate(temperatures):
        while waiting and temperatures[waiting[-1]] < temperature:
            earlier = waiting.pop()
            waits[earlier] = day - earlier
        waiting.append(day)
    return waits
