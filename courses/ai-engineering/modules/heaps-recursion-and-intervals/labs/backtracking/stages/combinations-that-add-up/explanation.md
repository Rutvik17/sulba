```python
def totals(numbers, target):
    numbers = sorted(numbers)
    found, chosen = [], []

    def extend(start, left):
        if left == 0:
            found.append(tuple(chosen))
            return
        for place in range(start, len(numbers)):
            number = numbers[place]
            if number > left:
                break
            if place > start and number == numbers[place - 1]:
                continue
            chosen.append(number)
            extend(place + 1, left - number)
            chosen.pop()

    extend(0, target)
    return found
```

Sorting first does two jobs. A number larger than what's left ends the loop, since every number after it is at least as large. And equal numbers sit side by side, so `place > start and number == numbers[place - 1]` skips a number equal to the one just tried for the same choice: choosing it would start the same combinations again. So each combination comes out once, in order, and the search never goes on past the target.

Trying every subset of the numbers is the slow way: {% $fig.subsets %} subsets of the tests' {% $fig.numbers %} numbers. Searching without skipping equal numbers is slow too: on the tests' {% $fig.ones %} ones and a target of {% $fig.half %}, it finds the one combination {% $fig.ways %} times.
