from bisect import bisect_right


class Calendar:
    def __init__(self):
        self.starts = []
        self.ends = []

    def book(self, start, end):
        place = bisect_right(self.starts, start)
        if place > 0 and self.ends[place - 1] > start:
            return False
        if place < len(self.starts) and self.starts[place] < end:
            return False
        self.starts.insert(place, start)
        self.ends.insert(place, end)
        return True
