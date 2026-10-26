Write `KthLargest`:

```
KthLargest(k, numbers) -> a stream that holds numbers, at least k - 1 of them, to start with
stream.add(number) -> adds the number, and gives the kth largest of all the numbers so far
```

With `stream = KthLargest(3, [4, 5, 8, 2])`, adding 3, 5, 10, 9 and 4 in turn gives 4, 5, 5, 8 and 8. A number added twice counts twice. The tests' longest stream takes {% $fig.adds %} numbers, with k at {% $fig.k %}.
