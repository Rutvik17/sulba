Before your team took the work on, an assistant wrote the office a value report: `report.py`'s `report(runs, variant)` gives a `Report` of the share of the office's contacts the desk does, the net it saves a month, and the months the pilot takes to pay for itself, each an `Estimate` with its interval. It takes the office's figures from your `mix.py` and `worth.py`. Its three tests all pass.

Review it as if the office were about to sign on its numbers: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office will read it. A run shows how many pass. You see which ones when you finish the review.

What the report must do:

- weight each kind by the office's contacts;
- take each kind's error over its tasks, each task counted once;
- take the fewest months from the most saved, and the most months from the least;
- count everything the desk costs the office.

```
report(runs, variant, volumes=OFFICE, minutes=MINUTES, agent=AGENT, host=HOST,
       support=SUPPORT, price=PRICE, confidence=0.95) -> Report
```
