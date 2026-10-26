def figures():
    posts, bad_share = 20_000, 0.02
    recall, precision = 0.9, 0.6
    bad = round(posts * bad_share)
    caught = round(bad * recall)
    flagged = round(caught / precision)
    return {
        "posts": f"{posts:,}",
        "bad_share": f"{bad_share:.0%}",
        "bad": f"{bad:,}",
        "recall": f"{recall:.0%}",
        "precision": f"{precision:.0%}",
        "caught": f"{caught:,}",
        "flagged": f"{flagged:,}",
        "wrongly": f"{flagged - caught:,}",
        "capacity": "600",
    }
