def two_groups(people, dislikes):
    """Whether the people, numbered from 0, can be split into two groups so that no two who
    dislike each other share one."""
    others = [[] for _ in range(people)]
    for first, second in dislikes:
        others[first].append(second)
        others[second].append(first)
    group = [None] * people
    for person in range(people):
        if group[person] is not None:
            continue
        group[person] = 0
        waiting = [person]
        while waiting:
            current = waiting.pop()
            for other in others[current]:
                if group[other] is None:
                    group[other] = 1 - group[current]
                    waiting.append(other)
                elif group[other] == group[current]:
                    return False
    return True
