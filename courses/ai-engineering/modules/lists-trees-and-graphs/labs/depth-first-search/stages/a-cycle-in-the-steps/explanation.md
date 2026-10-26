```python
def cycle(needs):
    done, on_path = set(), {}
    for start in needs:
        if start in done:
            continue
        path = [start]
        on_path[start] = 0
        waiting = [iter(needs.get(start, []))]
        while waiting:
            for step in waiting[-1]:
                if step in on_path:
                    return path[on_path[step] :] + [step]
                if step not in done:
                    on_path[step] = len(path)
                    path.append(step)
                    waiting.append(iter(needs.get(step, [])))
                    break
            else:
                waiting.pop()
                finished = path.pop()
                del on_path[finished]
                done.add(finished)
    return None
```

A depth-first walk from a step follows its needs, then theirs, keeping the steps on the current path in order, with each one's place in `on_path`. Reaching a step already on the path closes a cycle: the stretch of the path from that step on, and the step again. A step whose needs have all been followed is finished and leaves the path, since nothing it leads to comes back to the path, so reaching it again adds nothing. Each step and each need is followed once.

The walk keeps an iterator of each path step's needs on its own list, so the tests' chain of {% $fig.steps %} steps doesn't go a call deep per step, as a walk that calls itself would.
