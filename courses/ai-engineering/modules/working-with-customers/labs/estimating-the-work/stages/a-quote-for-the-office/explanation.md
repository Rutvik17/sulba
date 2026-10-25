The quote promises the office {% $fig.days %} working days, done by {% $fig.done_by %}, for {% $fig.price %}. Taking the 80th percentile up to whole days makes the promise a little safer than four in five: {% $fig.met %} of the runs finish within {% $fig.days %} days.

The price is the promised days at the day rate, so the spread of the work shows in the price as well as the date. A price for the likely plan's {% $fig.likely %} days would have been {% $fig.likely_price %}, and {% $fig.over_likely %} of the runs take longer than that.

Dates count working days only. Python's `date.weekday()` returns "the day of the week as an integer, where Monday is 0 and Sunday is 6", so a working day is one below 5 that isn't a day off. Stepping a day at a time from the start, the start included, reaches the last day after the days it needs; a start on a Saturday or a day off counts from the next working day.

Money stays in whole cents, as integers. Python's tutorial on floating point says "most decimal fractions cannot be represented exactly as binary fractions", so sums of dollars as floats drift, while integer cents add exactly. Each payment starts as its share rounded down, which leaves fewer cents than the price, and the cents left over go to the milestones that lost the most, one each: the payments add up to the price and each is within a cent of its share. Python's sorting guide says "The reverse parameter still maintains sort stability (so that records with equal keys retain the original order)", so sorting the milestones by remainder, largest first, keeps the earlier of two equal remainders first.

```python
def payments(price: int, milestones: dict[str, int]) -> dict[str, int]:
    total = sum(milestones.values())
    paid = {name: price * share // total for name, share in milestones.items()}
    left = price - sum(paid.values())
    remainders = sorted(
        milestones, key=lambda name: price * milestones[name] % total, reverse=True
    )
    for name in remainders[:left]:
        paid[name] += 1
    return paid
```
