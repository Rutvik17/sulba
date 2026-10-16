```python
def largest_run(numbers):
    best = ending = float("-inf")
    for number in numbers:
        ending = max(number, ending + number)
        best = max(best, ending)
    return best
```

`ending` is the largest sum of a run that ends at the current number. That run either starts at the number or extends the largest run ending just before it, so `ending` takes the larger of `number` and `ending + number`: a run whose sum is below zero only lowers what follows, so it's dropped. The answer is the largest `ending` over all the numbers, found in one pass with no extra space.

Starting both at minus infinity makes the first number the first run, so a list of negative numbers gives its largest number. Starting `best` at `0` would give `0`, the sum of a run of no numbers, which the problem doesn't allow.

Trying every run instead means {% $fig.runs %} runs for the longest test's {% $fig.numbers %} numbers, far past the time limit, even when each run's sum is built from the one before it.
