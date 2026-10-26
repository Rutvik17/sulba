The office's director reads the summary, not the code. In `summary.py`, write `summary(runs, variant, ...)`, its lines joined by newlines, from your `by_kind`, `weighted`, `seconds`, `monthly` and `payback`, with the arguments it's given:

```
The desk does <share> of the office's <contacts> contacts a month, from <low> to <high>.
<Kind>: <share> of <tasks> tasks, from <low> to <high>.
It saves <net> a month net, from <low> to <high>.
The pilot pays for itself in <months> months, from <low> to <high>.
```

- After the first line comes a line for each kind with contacts, in the order of `volumes`, by its name in `NAMES`. A kind's interval is its share less and plus `$z$` standard errors, within 0 and 1. A kind done in every trial is `<Kind>: all <tasks> tasks done in every trial.`, and one done in none `<Kind>: none of <tasks> tasks done in any trial.`
- Shares are in percent to a tenth, such as `57.7%`; dollars to the dollar, such as `$9,891`, or `-$985` for a loss; months to a tenth; and contacts with commas.
- Each estimate is rounded to the nearest with `round`, and each interval's ends outward: the low end down and the high end up.
- When the saving's low end is 0 or less, the last line is `The pilot pays for itself in <months> months, from <low>, or not at all at the saving's low end.` When the saving itself is, it's `At these figures the pilot doesn't pay for itself.`

What the summary must do:

- show intervals that hold the ones worked out;
- say in words when a kind's tasks never differ;
- say when the pilot may not pay for itself, or doesn't;
- use the figures it's given.

How it does so is yours to choose.

```
summary(runs, variant, volumes=OFFICE, minutes=MINUTES, agent=AGENT, host=HOST,
        support=SUPPORT, price=PRICE, confidence=0.95) -> str
```

Two tests run on every attempt. Then four checks run before the code ships.
