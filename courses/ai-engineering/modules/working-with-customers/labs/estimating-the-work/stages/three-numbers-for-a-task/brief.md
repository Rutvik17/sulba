A county's benefits office wants the help desk from this course in its contact centre, and has asked when a pilot could be running and what it will cost. Your team has broken the work into tasks and estimated each one in working days three ways: the fewest it could take, the most likely, and the most. This lab turns those estimates into a date the team can promise and a price.

Three numbers make a triangular distribution: its density rises in a straight line from `low` to `likely` and falls in a straight line to `high`. Writing `$a$`, `$c$` and `$b$` for `low`, `likely` and `high`, the chance that a task is done within `$d$` days is

```math
F(d) = \begin{cases} \dfrac{(d - a)^2}{(b - a)(c - a)} & a \le d \le c \\[1ex] 1 - \dfrac{(b - d)^2}{(b - a)(b - c)} & c \le d \le b \end{cases}
```

In `estimates.py`, write `mean(low, likely, high)`, the distribution's mean, and `quantile(low, likely, high, q)`, the days `$d$` within which the task is done with the chance `$q$`: the `$d$` for which `$F(d) = q$`. A task whose three estimates are equal takes exactly that many days.

Signing callers in through the office's directory is estimated at {% $fig.low %}, {% $fig.likely %} and {% $fig.high %} days. Its mean is {% $fig.mean %} days, and it's done within {% $fig.p80 %} days with a chance of 80%.

```
mean(low, likely, high) -> float
quantile(low, likely, high, q) -> float
```
