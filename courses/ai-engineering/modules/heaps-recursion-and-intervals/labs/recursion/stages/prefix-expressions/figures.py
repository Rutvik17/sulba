# The tests' longest and deepest expressions, as tests/test_expressions.py builds them.
GROUPS = 50_000
DEPTH = 300


def figures():
    longest = "(+ " + " ".join(f"(* {n} {n + 1})" for n in range(GROUPS)) + ")"
    return {
        "chars": f"{len(longest):,}",
        "groups": f"{GROUPS + 1:,}",
        "depth": f"{DEPTH}",
    }
