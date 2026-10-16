# The samples the memory check holds, and the most of the memory of objects without
# __slots__ that they may take, as checks/test_samples.py sets them.
SAMPLES = 20_000
SHARE = 0.75


def figures():
    return {"samples": f"{SAMPLES:,}", "share": f"{SHARE:.0%}"}
