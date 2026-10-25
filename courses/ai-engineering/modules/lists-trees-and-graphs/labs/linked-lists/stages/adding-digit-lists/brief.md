Each list holds a whole number's decimal digits, one a node, the ones digit first. Write `add`:

```
add(a, b) -> the head of a new list holding the digits of the two numbers' sum, the ones
    digit first
```

`2 → 4 → 3` is 342 and `5 → 6 → 4` is 465, so `add` of the two gives `7 → 0 → 8`, 807. The lists can have different lengths, neither has zeros at its end unless it's the number 0, a single `0`, and nor does the sum. Leave the lists as they were.

The tests' longest numbers have {% $fig.digits %} digits.
