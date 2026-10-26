def figures():
    customers, turns = 50_000, 4
    search_ms, max_calls = 80, 3
    return {
        "products": "40,000",
        "customers": f"{customers:,}",
        "turns": str(turns),
        "turns_day": f"{customers * turns:,}",
        "search_ms": str(search_ms),
        "max_calls": str(max_calls),
        "max_tool_ms": str(search_ms * max_calls),
        "dozen": "12",
    }
