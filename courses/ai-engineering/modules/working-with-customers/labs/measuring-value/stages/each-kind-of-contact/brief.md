The benefits office has its estimate and quote. Before it signs, it asks what the desk is worth to its contact centre. The figures come from the desk's own trials: `data/runs.csv` holds the desk's agent on {% $fig.tasks %} tasks, five trials each, where `variant` is `"agent"`. Each task is one kind of contact:

- `question`: a question answered from the services' pages;
- `case`: a check on an application, with a ticket opened once the caller says yes;
- `callback`: a callback booked on the caller's ticket, once they say yes;
- `new`: a new ticket and a call booked on it, once they say yes;
- `vague`: a callback asked for without saying what about, where the desk must change nothing.

A trial's `outcome` is `"done"` when it did the task, and otherwise says what went wrong.

A task's trials aren't separate samples of the office's contacts: five runs of one task share its wording, its page and its difficulty. So each task counts once. In `kinds.py`, write `by_kind(runs, variant)`, a `Share` for each kind, in the order the kinds first appear:

- `value`, the mean over the kind's tasks of each task's share of its trials done;
- `error`, the standard error of that mean: the standard deviation of the tasks' shares, as `statistics.stdev` gives it, over the square root of the number of tasks;
- `tasks`, the number of tasks.

A kind with fewer than two tasks raises `ValueError`, since one task can't show how much tasks differ.

| Kind | Tasks | Done | Standard error, points |
| --- | --- | --- | --- |
| Questions | {% $fig.question_tasks %} | {% $fig.question_done %} | {% $fig.question_error %} |
| Cases | {% $fig.case_tasks %} | {% $fig.case_done %} | {% $fig.case_error %} |
| Callbacks | {% $fig.callback_tasks %} | {% $fig.callback_done %} | {% $fig.callback_error %} |
| New tickets | {% $fig.new_tasks %} | {% $fig.new_done %} | {% $fig.new_error %} |
| Vague requests | {% $fig.vague_tasks %} | {% $fig.vague_done %} | {% $fig.vague_error %} |

```
by_kind(runs, variant) -> dict[str, Share]
```
