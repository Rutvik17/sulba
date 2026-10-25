The desk changes its agent only when the change is shown to do no harm. A release gate decides from both agents' trials of the same tasks: a candidate may replace the current agent only if its pass^k can't be much lower, and its slow tenth can't be over the desk's budget.

In `gate.py`, write `gate(runs, current, candidate, k=..., tolerance=..., seconds=...)`, which gives a `Verdict`:

- `difference`, a `Score`: over the tasks, the mean of the candidate's pass^k less the current agent's on each task, with the mean less and plus z standard errors of those differences, z for the confidence;
- `tail`, a `Score`: the candidate's 90th percentile of seconds over each task's median, with its interval, from your `costs.py`;
- `held`, what the candidate is held for, in this order: `"pass^k"` when the difference's low end is below `-tolerance`, and `"seconds"` when the tail's high end isn't within `seconds`. A candidate held for nothing ships.

What the gate must do:

- compare the two agents task by task;
- hold a candidate for its pass^k only when it may be worse by more than the tolerance;
- hold a candidate whose 90th percentile it can't bound for its seconds;
- raise `ValueError` for agents that ran different tasks, or a task a different number of times, or any task fewer than k times.

How it does so is yours to choose.

```
gate(runs, current, candidate, k=..., tolerance=..., seconds=..., confidence=0.95) -> Verdict
verdict.ship -> bool
```

Three tests run on every attempt. Then four checks run before the code ships.
