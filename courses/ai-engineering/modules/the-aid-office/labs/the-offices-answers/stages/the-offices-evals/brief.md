The office wants its assistant to answer sooner on its own server, where reading a reply's prompt takes much of its time, and the passages make most of the prompt. Before the assistant is given three passages instead of five, the office wants to know what that costs in answers. An eval tells it, from both releases' replies to the same questions.

`data/shown.csv` holds the passages each of the office's {% $fig.questions %} questions' replies were given: the best passage of each of its five best pages by meaning, each with its `number`, from 1, and its `page`. `data/replies.csv` holds each question's `reply` from two releases, both Qwen3.5-0.8B with your `answers.py`'s instructions and message: `five`, given the five passages, and `three`, given the first three. Each reply has the reason the model stopped, the `prompt_tokens` it read and the `reply_tokens` it wrote.

In `evals.py`, write:

- `outcome(reply, shown, page)`: how a reply went, `shown` giving the page of each passage it was given, in order, and `page` the question's own: `"staff"` when your `answer` would pass it to staff, `"right"` when it cites the question's page, and `"wrong"` when it cites only other pages.
- `outcomes(replies, shown, questions, release)`: each question's outcome in the release, in the order of `questions`, from the rows of `replies.csv`, `shown.csv` and `questions.csv` as `csv.DictReader` gives them. A release gave the model its question's first `RELEASES[release]` passages.
- `shares(found)`: the share of the outcomes that are each of `OUTCOMES`.
- `change(baseline, candidate, pages, name, confidence)`: the candidate's share of the outcome `name` less the baseline's, on the same questions, with its margin at the `confidence` asked, as a `Change`.

`change` takes each question's difference, `$d_i$`, 1 when only the candidate's outcome is `name`, -1 when only the baseline's is, and 0 otherwise, so what the questions share drops out, and the change, `$c$`, is their mean. Questions about one page share its passages, so the standard error counts each page's questions together, with `$G$` the number of pages and `$n$` of questions, and the margin is the standard error times the `$z$` that leaves `(1 - confidence) / 2` of the normal distribution above.

```math
c = \frac{1}{n} \sum_i d_i \qquad \mathrm{SE} = \frac{1}{n} \sqrt{\frac{G}{G - 1} \sum_{g} \Big( \sum_{i \in g} (d_i - c) \Big)^2}
```

```
outcome(reply, shown, page) -> "right", "wrong" or "staff"
outcomes(replies, shown, questions, release) -> list of outcomes
shares(found) -> dict of shares
change(baseline, candidate, pages, name, confidence) -> Change
```
