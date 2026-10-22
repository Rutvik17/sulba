```python
def add(a, b):
    before = tail = Node(None)
    carry = 0
    while a is not None or b is not None or carry:
        total = carry
        if a is not None:
            total += a.value
            a = a.next
        if b is not None:
            total += b.value
            b = b.next
        carry, digit = divmod(total, 10)
        tail.next = Node(digit)
        tail = tail.next
    return before.next
```

The digits come ones first, the order addition needs, so one walk down both lists adds them as on paper. A digit pair and the carry add to at most 19, so the carry is never more than 1. The loop runs once per digit of the longer number, and once more for a last carry: time and space in proportion to the sum's digits.

Turning each list into a Python `int` and back looks shorter, and fails on the longest test, whose numbers have {% $fig.digits %} digits. Through a string, Python refuses to turn a string of more than {% $fig.limit %} digits into an `int`, or such an `int` into a string: "The default limit is 4300 digits as provided in sys.int_info.default_max_str_digits." Its documentation gives the reason: "There exists no algorithm that can convert a string to a binary integer or a binary integer to a string in linear time, unless the base is a power of 2." Through arithmetic, a digit at a time, each step multiplies the whole number so far by 10, so the work grows with the square of the number's digits, and runs out of time.
