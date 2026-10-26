How long a student waits for an answer, and how many questions an hour the desk can take, decide whether one server is enough for the office. `data/timings.csv` holds what the model server timed for each of the two releases' {% $fig.requests %} requests, sent one at a time, every question in turn for one release and then the other, on 4 cores of an Intel Xeon at 2.1 GHz. Each row has its `question` and `release`; the prompt tokens the server took from its cache, `cache_n`, and those it processed, `prompt_n`, in `prompt_ms` milliseconds; and the tokens it wrote, `predicted_n`, in `predicted_ms`.

In `capacity.py`, write:

- `read(path)`: each row's `Timing`, in order: its question and release, `first`, the seconds to the reply's first piece, which are the prompt's time and one token's, and `whole`, the seconds to the whole reply. A reply of no tokens takes its prompt's time alone.
- `percentile(values, share)`: the smallest of the values that at least `share` of them are at or below.
- `per_hour(seconds)`: how many replies an hour one server writes, one after another, at the seconds each takes.
- `busy(peak, hourly)`: the share of an hour of `peak` questions that a server writing `hourly` replies an hour spends replying.

```
read(path) -> list of Timing
percentile(values, share) -> value
per_hour(seconds) -> float
busy(peak, hourly) -> float
```
