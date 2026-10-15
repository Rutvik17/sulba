The plant schedules its output a day ahead, and a single number doesn't say how far off it may be. Ship the forecaster with an interval around each forecast that holds the actual output a stated share of the time.

`halfwidth` takes the misses, actual output minus forecast, on `n` hours the model didn't fit, and returns how far either side of a forecast the interval reaches: the `ceil((n + 1) * coverage)`-th smallest miss size, or `inf` when that is more than `n`.

`intervals` returns the low and high ends of each hour's interval, the forecast minus and plus `q`.

```
halfwidth(misses, coverage=0.9) -> float
intervals(forecaster, weather, q) -> (low, high)
```

Hidden tests check both functions. Then the checks fit a forecaster on four of every five training hours, take the misses on the fifth, and test the intervals on the test hours.
