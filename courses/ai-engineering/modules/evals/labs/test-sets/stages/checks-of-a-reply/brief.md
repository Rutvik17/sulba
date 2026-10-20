The help desk's current release replied once to each question. `data/replies.csv` holds each reply, with the reason the model stopped: `stop` when it ended the reply itself, or `length` when it reached its limit of {% $fig.limit %} tokens. `data/shown.csv` holds the {% $fig.shown %} passages it was shown for each question, in order, and `data/relevant.csv` the passages that hold each answer. Its prompt asks for an answer in two or three sentences, from the passages alone, that cites each passage it uses by its name in square brackets, such as `[p12]`.

Some of what makes a reply good can be checked in code, on every reply of every release, at no cost. In `checks.py`, write:

- `cited(reply)`: the passages the reply cites, each a `p` and its number in square brackets, each once, in the order it first cites them.
- `checks(reply, finish, shown, relevant, most)`: whether the reply passes each of five checks, by name:
  - `cites`: it cites a passage;
  - `cites_shown`: it cites only passages it was shown;
  - `cites_answer`: a passage it cites holds the answer;
  - `finished`: the model ended it itself;
  - `brief`: it has at most `most` words, as `str.split` divides them.
- `pass_rates(results)`: each check's share of the replies that pass it, and `all`, the share that pass every check.

```
cited(reply) -> list of passages
checks(reply, finish, shown, relevant, most) -> {check: passed}
pass_rates(results) -> {check: share}
```
