A gate stops a release when its drop is too large to be noise: when a one-sided test at level `alpha` finds the change below zero. A real drop of only a standard error or two is often missed, since chance moves its estimate by as much. The help desk needs to know how large a drop its test set finds most of the time, and how many questions a smaller one would take.

In `power.py`, write:

- `detectable(error, alpha, power)`: the smallest drop a one-sided test at level `alpha` finds with probability `power`, for a change whose standard error is `error`.
- `questions_needed(error, questions, drop, alpha, power)`: the fewest questions on which the test finds `drop` with probability `power`, when `questions` questions give a standard error of `error` and more questions spread as these do, so that the standard error shrinks with the square root of their number.

```math
\begin{aligned}
\delta &= (z_{1-\alpha} + z_{\text{power}}) \cdot \mathrm{SE} \\
n' &= \Bigl\lceil n \Bigl( \frac{\delta}{\text{drop}} \Bigr)^2 \Bigr\rceil
\end{aligned}
```

`z_p` is the value the standard normal distribution falls below with probability `p`. The tests compare your drops with the effects at which statsmodels' `NormalIndPower` gives a one-sided test its power.

```
detectable(error, alpha, power) -> float
questions_needed(error, questions, drop, alpha, power) -> int
```
