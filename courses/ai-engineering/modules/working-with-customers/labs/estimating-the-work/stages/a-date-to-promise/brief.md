The office wants the pilot running within {% $fig.deadline %} working days. With every task at its likely days the plan says {% $fig.likely %}, but the simulation tells a different story. In `promise.py`, write two functions of a list of simulated finishes:

- `promised(finishes, chance)`: the fewest days within which at least the share `chance` of the runs finish, which is one of the runs' finishes: the smallest `$x$` such that at least `$\lceil \text{chance} \times n \rceil$` of the `$n$` runs finish within `$x$`;
- `chance_by(finishes, day)`: the share of the runs that have finished by the end of `day`, a finish on the day itself counting.

Over the {% $fig.runs %} runs from seed 0, half the runs finish within {% $fig.p50 %} days and four in five within {% $fig.p80 %}.

```
promised(finishes, chance) -> float
chance_by(finishes, day) -> float
```
