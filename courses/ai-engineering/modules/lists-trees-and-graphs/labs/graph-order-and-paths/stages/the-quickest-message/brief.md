A network's computers are numbered from 1 to `computers`, and `links` lists one-way links `(source, target, minutes)`: a message at `source` reaches `target` that many minutes later, at least 0. A message sent from `start` goes out along every link at once, and each computer passes it on as soon as it arrives. Write `delay`:

```
delay(computers, links, start) -> the minutes until the message has reached every computer,
    or -1 if some computer never gets it
```

With 4 computers, the links `[(2, 1, 1), (2, 3, 1), (3, 4, 1)]` and a start at 2, every computer has the message after 2 minutes. If the start were 1, which has no links out, the answer would be -1. The tests' largest network has {% $fig.computers %} computers and {% $fig.links %} links.
