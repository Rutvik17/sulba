```python
def merged(accounts):
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
```

Addresses, not names, decide who's who, so the groups are found among addresses: union-find joins each account's addresses to its first, and two accounts that share an address end up joined through it, however long the chain of accounts between them. The name comes from any address of the group, since every address of one person has that person's name. Each address takes a `find` or two, and halving the paths as they're walked keeps those walks short; sorting each person's `a` addresses takes time in proportion to `$a \log a$`.

Comparing every pair of accounts, and merging any two that share an address until no more merge, is the slow way. On the longest test's chain of {% $fig.accounts %} accounts, the first pass alone compares {% $fig.pairs %} pairs.
