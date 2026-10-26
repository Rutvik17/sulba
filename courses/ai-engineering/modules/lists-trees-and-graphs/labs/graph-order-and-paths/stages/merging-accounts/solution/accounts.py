def merged(accounts):
    """Each person's accounts merged into one: their name, then all their addresses, sorted."""
    leader = {}

    def find(address):
        while leader[address] != address:
            leader[address] = leader[leader[address]]
            address = leader[address]
        return address

    owner = {}
    for name, *addresses in accounts:
        for address in addresses:
            if address not in leader:
                leader[address] = address
                owner[address] = name
            leader[find(address)] = find(addresses[0])
    groups = {}
    for address in leader:
        groups.setdefault(find(address), []).append(address)
    return [[owner[root], *sorted(group)] for root, group in groups.items()]
