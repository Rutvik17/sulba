```python
def addresses(digits):
    found, parts = [], []

    def extend(start):
        if len(parts) == 4:
            if start == len(digits):
                found.append(".".join(parts))
            return
        for end in range(start + 1, min(start + 3, len(digits)) + 1):
            part = digits[start:end]
            if (len(part) > 1 and part[0] == "0") or int(part) > 255:
                break
            parts.append(part)
            extend(end)
            parts.pop()

    extend(0)
    return found
```

An address is four numbers, so the search chooses each number's digits in turn, one to three of them, and an address is finished when the fourth number ends exactly at the last digit. A number with a leading zero, or over 255, ends the loop: a longer number from the same place keeps the same leading zero, or is larger still. With at most 3 ways to choose each of 4 numbers, the search tries at most $3^4$ ways however long the digits are, so a string too long to be an address costs almost nothing. Trying the shorter number first gives the addresses in sorted order, since a dot sorts before every digit.

Trying every way to put three dots among the digits is the slow way: for the tests' longest string, {% $fig.ways %} ways.
