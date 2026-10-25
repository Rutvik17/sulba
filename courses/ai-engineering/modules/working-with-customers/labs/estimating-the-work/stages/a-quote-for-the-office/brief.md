The office reads its quote as a date and a price. In `quote.py`, write `quote(finishes, ...)`, which gives a `Quote` for a project's simulated finishes:

- `days`, the fewest whole working days by which at least four runs in five finish;
- `done_by`, the last of those days, counted from `start`, which is the first of them if it's a working day;
- `price`, the days at `day_rate`, in cents;
- `payments`, the price split between the milestones by their shares, in cents.

Work starts on {% $fig.start %}, the team's day rate is {% $fig.rate %}, and besides Saturdays and Sundays the team doesn't work on {% $fig.off %}. The office pays in thirds: when it signs, at the demo, and once the pilot is running. Over the {% $fig.runs %} runs from seed 0, the quote is {% $fig.days %} working days, done by {% $fig.done_by %}, for {% $fig.price %}: {% $fig.signed %}, {% $fig.demo %} and {% $fig.running %}.

What the quote must do:

- round the days up to whole days;
- count only working days: no Saturdays, Sundays or days off;
- make the payments add up to the price exactly: each milestone gets its share rounded down to the cent, and each cent left over goes to a milestone with the largest remainder, the earlier on a tie;
- raise `ValueError` for no finishes, a day rate of 0 or less, no milestones, or a share of 0 or less.

How it does so is yours to choose.

```
quote(finishes, start=START, day_rate=DAY_RATE,
      milestones=MILESTONES, days_off=DAYS_OFF) -> Quote
```

Three tests run on every attempt. Then four checks run before the code ships.
