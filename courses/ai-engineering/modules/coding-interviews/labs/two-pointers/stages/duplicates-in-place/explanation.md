```python
def dedupe(numbers):
    kept = 0
    for number in numbers:
        if kept == 0 or number != numbers[kept - 1]:
            numbers[kept] = number
            kept += 1
    return kept
```

`kept` counts the different values written so far, and is where the next one goes. In a sorted list, a value is new exactly when it differs from the last one written, so each new value is copied forwards once. Writing never gets ahead of reading, since `kept` is never past the number being read, so no value is overwritten before it's read. One pass, and no space besides `kept`.

Deleting each repeat with `del numbers[i]` instead shifts every item after it back by one: for the longest test, which holds each value twice, that's {% $fig.moves %} moves, far past the time limit.
