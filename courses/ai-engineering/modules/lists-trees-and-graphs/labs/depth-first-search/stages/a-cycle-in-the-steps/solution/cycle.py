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
