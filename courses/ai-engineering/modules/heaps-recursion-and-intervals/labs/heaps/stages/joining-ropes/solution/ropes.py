import heapq


def join_cost(lengths):
    ropes = list(lengths)
    heapq.heapify(ropes)
    cost = 0
    while len(ropes) > 1:
        joined = heapq.heappop(ropes) + heapq.heappop(ropes)
        cost += joined
        heapq.heappush(ropes, joined)
    return cost
