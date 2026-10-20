The help desk will report each release on its test set: the share of the replies that pass every check, over all the questions and for each service, each with its margin of error at {% $fig.confidence %}. It wants each margin within ±{% $fig.target %}, and where a margin isn't, the report says how many questions a test set like this one would need.

In `release.py`, write:

- `line(scores, pages, target, confidence)`: a `Line` for a group of questions, from their scores, 1 for a reply that passes every check and 0 for one that doesn't, and their pages. `rate` is the scores' mean, `margin` its margin of error at `confidence` with each page's questions counted together, `questions` how many there are, and `needed` the fewest questions whose margin would be within `target`. With the same spread and the same pull of a page's questions together, a margin falls as one over the square root of the questions.
- `report(results, pages, services, target, confidence)`: a line for every question, named `all`, then one for each service in alphabetical order, from its own questions. `results` maps each question to its checks, as `checks` gives them, and `pages` and `services` map each question to its page and its service.

```
line(scores, pages, target, confidence) -> Line
report(results, pages, services, target, confidence) -> {name: Line}
```

Two tests run on every attempt. Then four checks run before the code ships.
