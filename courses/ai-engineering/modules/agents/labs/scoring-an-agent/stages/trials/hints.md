`math.comb(n, k)` is `$\binom{n}{k}$`, and it's 0 when k is more than n, which is what pass^k needs when fewer than k trials did the task.

---

A score's standard error is the standard deviation of the tasks' estimates over the square root of how many tasks there are; `NormalDist().inv_cdf((1 + confidence) / 2)` is z.
