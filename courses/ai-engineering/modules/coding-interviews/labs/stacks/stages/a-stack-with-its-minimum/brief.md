Write a class `MinStack`, a stack that also knows its smallest value:

```
MinStack() -> an empty stack
push(value) -> puts value on top
pop() -> takes the top value off and returns it
top() -> the top value
minimum() -> the smallest value on the stack
```

Each takes constant time, however many values the stack holds. `pop`, `top` and `minimum` raise `IndexError` on an empty stack.

```python
stack = MinStack()
stack.push(5)
stack.push(2)
stack.push(7)
stack.minimum()  # 2
stack.pop()  # 7
stack.pop()  # 2
stack.minimum()  # 5
```

The tests' longest run pushes {% $fig.values %} values, asking for the minimum after each.
