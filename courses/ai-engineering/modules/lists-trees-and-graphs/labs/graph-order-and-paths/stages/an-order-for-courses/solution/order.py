from collections import deque


def course_order(courses, prerequisites):
    """Every course, numbered from 0, in an order that takes each after the courses it needs,
    or an empty list if there's no such order."""
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
