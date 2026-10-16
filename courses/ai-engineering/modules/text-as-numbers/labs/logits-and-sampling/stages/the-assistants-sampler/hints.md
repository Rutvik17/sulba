For one pair, compare `warp(values, 0.5, top_p=1.0)` with `warp(values, 2.0, top_p=1.0)`, then `warp(values, top_p=0.8)` with `judge.warp(values, 0.7, 20, 0.8)`, your `warp` from stage 2.

---

Draw from `np.array([0.9, 0.1])` many times with one generator, and count each index. Then label many copies of one pair whose two answers are equally likely.
