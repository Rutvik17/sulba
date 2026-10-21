The help desk's CI will run the gate on every release before it ships, as a command:

```sh
uv run release_gate.py <file of replies> <baseline> <candidate>
```

It scores both releases' first {% $fig.samples %} samples on {% $fig.scores %} scores, compares each with your `gate`, prints a line for each and then its decision, and exits with 1 when it stops the candidate, which fails the CI job, and with 0 when the candidate ships. A rerun of a release no worse than the baseline can be stopped on any of them: gated each at `alpha`, together they would stop such a release more often than `alpha`. Gated each at `alpha` over the number of scores, the chance that any of them stops it is at most `alpha`.

In `release_gate.py`, write:

- `scored(replies, relevant, questions, release, samples)`: the release's scores by name, each an array as `scores` gives it: `cites_answer`, as `cites_answer` scores a reply; `finished`, 1.0 when the model ended the reply itself, its `finish` being `stop`; and `brief`, 1.0 for a reply of at most {% $fig.most %} words, as `str.split` divides them.
- `check(baseline, candidate, pages, alpha)`: a `Verdict` on each score, by name, from `gate` at `alpha` over the number of scores.
- `report(verdicts)`: a line for each score, in their order, as `name: change (low to high), ships` or `stopped`, each number with its sign and three decimals, then `ships` if every score ships and `stopped` if not.
- `main(arguments)`: the command, from its three arguments, with the questions, pages and passages in `data/`, at an `alpha` of {% $fig.alpha %}: prints the report's lines and returns 1 when it stops the candidate and 0 when it ships.

```
cites_answer: <change> (<low> to <high>), ships
finished: <change> (<low> to <high>), stopped
brief: <change> (<low> to <high>), ships
stopped
```

```
scored(replies, relevant, questions, release, samples) -> {name: array}
check(baseline, candidate, pages, alpha) -> {name: Verdict}
report(verdicts) -> [line]
main(arguments) -> int
```
