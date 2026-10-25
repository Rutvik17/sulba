```python
def two_groups(people, dislikes):
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
```

People and their dislikes make a graph, and the question is whether its nodes can take two colours with no link joining the same colour, which is to say whether it's bipartite. Within a part of the graph that hangs together, the first person's group decides everyone else's, so the search tries only the choices it's forced to, and a dislike between two people of the same group proves no split exists. People who share no dislike with anyone searched so far start a part of their own, and its first group is free. Each person and each dislike is handled once or twice: time and space in proportion to them.

Trying every split is the slow way. Each person goes in one group or the other, so even 40 people can be split {% $fig.splits %} ways.
