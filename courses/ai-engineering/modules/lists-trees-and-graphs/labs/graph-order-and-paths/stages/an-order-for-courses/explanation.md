```python
from collections import deque


def course_order(courses, prerequisites):
    needed_by = [[] for _ in range(courses)]
    waiting_on = [0] * courses
    for course, before in prerequisites:
        needed_by[before].append(course)
        waiting_on[course] += 1
    ready = deque(course for course in range(courses) if waiting_on[course] == 0)
    order = []
    while ready:
        course = ready.popleft()
        order.append(course)
        for later in needed_by[course]:
            waiting_on[later] -= 1
            if waiting_on[later] == 0:
                ready.append(later)
    return order if len(order) == courses else []
```

An order like this is a topological sort of the graph whose links run from each prerequisite to the course that needs it, and this way of finding one is Kahn's algorithm. A course joins the order only once every course it needs is in it, so the order keeps every prerequisite. If some courses need each other, directly or round a longer loop, none of them ever reaches 0, and the order comes up short. Each course and each prerequisite is handled once: time and space in proportion to them.

Looking through every course for one that's ready, each time one is taken, is the slow way. For the largest test's chain that's a pass over the courses left for each of its {% $fig.courses %} courses, {% $fig.looks %} looks in all. A depth-first search that adds each course after the ones it needs works too, if it keeps its own list of courses to visit: written as a function that calls itself, it follows the largest test's chain {% $fig.courses %} calls deep, past the recursion limit Python starts with.
