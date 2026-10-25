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
