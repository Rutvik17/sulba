# The waits of the shop's client: the first, after the first attempt, and the longest. The
# Retry-After of the check on waiting.
FIRST, MOST, ASKED = 1, 8, 3
# The openai package's own retries, from openai/_constants.py in version 2.30.0: how many, the
# first wait in seconds, and the longest.
OPENAI, RETRIES, OPENAI_FIRST, OPENAI_MOST = "2.30.0", 2, 0.5, 8.0


def figures():
    return {
        "first": str(FIRST),
        "most": str(MOST),
        "asked": str(ASKED),
        "openai": OPENAI,
        "retries": str(RETRIES),
        "openai_first": str(OPENAI_FIRST),
        "openai_most": f"{OPENAI_MOST:g}",
    }
