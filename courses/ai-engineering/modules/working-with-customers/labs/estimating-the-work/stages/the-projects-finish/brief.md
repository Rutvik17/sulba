The team's estimates for the office's pilot are in `schedule.py`'s `OFFICE`, a list of `Task`s, each after the tasks it waits for. A task starts once every task it waits for has ended, and tasks that wait for nothing between them run side by side.

| Task | Low | Likely | High | Waits for |
| --- | --- | --- | --- | --- |
| pages | 2 | 3 | 6 | |
| sign-in | 3 | 5 | 12 | |
| answers | 4 | 6 | 10 | pages |
| test set | 3 | 4 | 8 | pages |
| gates | 2 | 3 | 5 | answers, test set |
| chat page | 3 | 4 | 7 | sign-in |
| review | 2 | 4 | 10 | sign-in, answers |
| deploy | 2 | 3 | 8 | gates, chat page, review |
| pilot | 5 | 5 | 7 | deploy |

In `schedule.py`, write two functions. `finish(tasks, days)` gives the day the last task ends when each task takes `days[name]` days, counting from day 0. With every task at its likely days, the pilot ends on day {% $fig.likely %}.

`simulate(tasks, runs, seed)` gives the finish of each of `runs` runs of the project, each with every task's days drawn at random from its triangular distribution. Make one `random.Random(seed)` for the simulation and, in each run, draw the tasks in the list's order with its `triangular` method, so the same seed gives the same runs. Over {% $fig.runs %} runs with seed 0, the pilot ends on day {% $fig.mean %} on average.

```
finish(tasks, days) -> float
simulate(tasks, runs, seed) -> list[float]
```
