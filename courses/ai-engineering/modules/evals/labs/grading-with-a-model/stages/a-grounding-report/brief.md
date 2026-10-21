The help desk will grade each release's replies with the grader before it ships, and report the share the grader calls ungrounded, over all the questions and for each service, each with its margin of error, and the replies for people to read. A reply is graded with the passages it was written from: the first {% $fig.shown %} the search ranked for its question, each as its name in square brackets and its page's title, then its text on the next line, with a blank line between passages.

In `grounding.py`, write:

- `shown(names, passages)`: the passages named, in that form.
- `risks(client, chat, replies, passages, ranked, today)`: the grader's risk for each question's reply, with the passages shown with it, from your `judge.graded`. `replies` maps each question to its reply, and `ranked` maps it to the passages the search ranked for it, in order.
- `line(flags, pages, confidence)`: a `Line` for a group of replies, from their flags, 1 for a reply the grader calls ungrounded and 0 for one it doesn't, and their questions' pages. `flagged` is the flags' mean, `margin` its margin of error at `confidence`, with each page's replies counted together, and `replies` how many there are.
- `report(risks, questions, threshold, confidence)`: a line for every reply, named `all`, then one for each service in alphabetical order, from its own replies. A reply is flagged when its risk is at or above `threshold`, and `questions` maps each question to its row of `data/questions.csv`.
- `to_read(risks, threshold)`: the questions whose replies are flagged, the highest risk first, in the order of `risks` where two tie.

With `$n$` replies on `$G$` pages, `$e_i$` each flag less their mean, and `$z$` the normal distribution's quantile for the confidence, the margin is:

```math
\text{margin} = \frac{z}{n} \sqrt{\frac{G}{G - 1} \sum_{g} \left(\sum_{i \in g} e_i\right)^2}
```

```
shown(names, passages) -> str
risks(client, chat, replies, passages, ranked, today) -> {question: float}
line(flags, pages, confidence) -> Line
report(risks, questions, threshold, confidence) -> {name: Line}
to_read(risks, threshold) -> [question]
```

Two tests run on every attempt. Then four checks run before the code ships.
