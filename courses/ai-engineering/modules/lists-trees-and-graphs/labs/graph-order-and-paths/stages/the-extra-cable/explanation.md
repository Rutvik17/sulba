```python
def extra_cable(cables):
    leader = list(range(len(cables) + 1))

    def find(computer):
        while leader[computer] != computer:
            leader[computer] = leader[leader[computer]]
            computer = leader[computer]
        return computer

    for first, second in cables:
        a, b = find(first), find(second)
        if a == b:
            return (first, second)
        leader[a] = b
    raise ValueError("The cables make no loop.")
```

This is union-find, or a disjoint-set forest: each group of joined computers is a tree of links to its leader, `find` follows a computer's links to it, and a cable either finds its ends already in one group or joins their two groups into one. The cables that would do are the loop's, and the loop is first closed by the last of them in the list, the first cable whose ends are already joined, so that's the answer. While it walks, `find` points each computer it passes at the one two steps on, which keeps the trees short, so the walks stay short even for a long chain of cables.

Searching from one end of each cable to see whether the other is already reachable is the slow way: for the largest test's {% $fig.computers %} computers, joined in a chain before the loop closes, the searches visit {% $fig.visits %} computers in all.
