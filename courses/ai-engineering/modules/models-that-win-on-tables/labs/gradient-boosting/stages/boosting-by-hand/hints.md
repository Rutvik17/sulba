`np.log(share / (1 - share))` is the log-odds of a share. Keep each call's log-odds in an array that starts at `start(said_yes)` for every call.

---

`tree.apply(X)` gives each row's leaf, as a node number. An array of `tree.tree_.node_count` zeros, with each leaf's value at its node number, gives every row its value as `values[tree.apply(X)]`.

---

Each round's shares come from the log-odds after the round before, so update the log-odds at the end of each round, and keep the trees and their values in the model in the order they were grown.
