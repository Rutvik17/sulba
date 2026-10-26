The office decides which release to run from a write-up: how well each release answers, how fast, and what that means for its busiest hour, {% $fig.peak %} questions last term. Write it in `report.py`:

- `report(data=Path("data"))`: the `Report`, from the files in `data`: the office's `questions`, how many; each release's `Release`, five's first; `wrong`, three's share wrong less five's, as the office's `evals.py` gives it with `change`, at `CONFIDENCE`; and `chosen`, the release `to_run` gives.
- `to_run(wrong)`: the release to run: `"three"`, the faster, unless the interval of `wrong`, from its change less its margin to its change plus it, lies wholly above 0, and then `"five"`.
- `markdown(report)`: the write-up in Markdown, as the tests show it: a heading, what the figures are, a table of the releases, and the decision with the change and its margin.

A `Release` holds its `name`; its shares `right`, `wrong` and `staff`, by `evals.py`'s `outcomes` and `shares`; `first` and `whole`, the seconds within which `SLOWEST` of its replies give their first piece and their whole reply, by your `percentile`; `hourly`, by your `per_hour` of its whole replies; and `busy`, its share of the busiest hour, by your `busy`.

```
report(data=Path("data")) -> Report
to_run(wrong) -> "five" or "three"
markdown(report) -> str
```

Two tests run on every attempt. Then four checks, which work each figure out again from the files, run before the write-up goes to the office.
