# The tests' longest list, as tests/test_cooldown.py sets it.
COMMONEST = 50_000
OTHERS = 50_000
COOLDOWN = 100


def figures():
    units = (COMMONEST - 1) * (COOLDOWN + 1) + 1
    return {"tasks": f"{COMMONEST + OTHERS:,}", "units": f"{units:,}"}
