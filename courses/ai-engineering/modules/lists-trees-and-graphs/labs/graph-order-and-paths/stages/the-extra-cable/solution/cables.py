def extra_cable(cables):
    """The last cable in the list without which the computers are still all joined, with no
    loop."""
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
