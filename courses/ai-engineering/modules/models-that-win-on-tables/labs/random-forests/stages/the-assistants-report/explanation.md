The assistant's tests checked that `grow` gives a tree for each sample, that `score` averages, and that `importance` gives every column a number, without looking at what the samples, the estimate or the numbers were. The checks used the report as the bank will: comparing the trees, estimating from calls the trees didn't see, measuring on the validation calls, and running it again.

---

A forest's randomness is part of the model. Its trees need samples drawn independently, from one generator seeded once, so that the forest can be grown again exactly. And every number in its report is measured on calls the trees haven't seen: out of bag for the AUC, and the validation calls for the importances.
