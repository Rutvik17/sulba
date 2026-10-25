# The longest test, as tests/test_cycle.py sets it, and the memory it allows the call.
NODES = 200_000
ALLOWED = 64 * 1024


def figures():
    return {"nodes": f"{NODES:,}", "allowed": f"{ALLOWED // 1024} KiB"}
