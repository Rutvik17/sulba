import heapq


class KthLargest:
    def __init__(self, k, numbers):
        self.k = k
        self.largest = heapq.nlargest(k, numbers)
        heapq.heapify(self.largest)

    def add(self, number):
        if len(self.largest) < self.k:
            heapq.heappush(self.largest, number)
        elif number > self.largest[0]:
            heapq.heapreplace(self.largest, number)
        return self.largest[0]
