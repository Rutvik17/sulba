An agent's run of a task depends on the model's sampling, so the same task, run again, can come out otherwise. Scoring an agent once a task measures how often it gets a task right, not whether it can be relied on. Run each task several times, and two scores tell those apart: pass@k, the chance that at least one of k trials does the task, and pass^k, the chance that all k do.

In `scores.py`, write:

- `pass_at_k(n, c, k)` and `pass_hat_k(n, c, k)`, a task's pass@k and pass^k from its `n` trials, `c` of which did the task: `$1 - \binom{n - c}{k} / \binom{n}{k}$` and `$\binom{c}{k} / \binom{n}{k}$`, where `$\binom{n}{k}$` is the number of ways to choose `$k$` of `$n$`. Each raises `ValueError` unless k is from 1 to n and c from 0 to n.
- `trials(runs, variant)`, from `runs.csv`'s rows, each task's `(n, c)` for the variant: its trials and how many of them were `"done"`.
- `score(counts, k, every=True, confidence=0.95)`, pass^k averaged over the tasks, or pass@k when `every` is `False`, as a `Score`: the mean of the tasks' estimates, with the mean less and plus z standard errors of the tasks' estimates, z for the confidence.

```
pass_at_k(n, c, k) -> float
pass_hat_k(n, c, k) -> float
trials(runs, variant) -> dict[str, tuple[int, int]]
score(counts, k, every=True, confidence=0.95) -> Score
```
