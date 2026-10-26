def figures():
    searches, search_s, rounds = 8, 3, 2
    return {
        "countries": "12",
        "visitors": "30,000",
        "searches": str(searches),
        "search_s": str(search_s),
        "rounds": str(rounds),
        "serial_s": str(searches * search_s),
        "parallel_s": str(rounds * search_s),
        "hold_minutes": "15",
    }
