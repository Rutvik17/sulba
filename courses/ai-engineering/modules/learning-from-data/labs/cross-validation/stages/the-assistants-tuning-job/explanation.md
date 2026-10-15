The assistant's tests checked that a pair is chosen from the grid, that the expected error is a number of MPa, and that the model gives a strength per test, so they passed. The plant relies on more: on records without the tests that stand in for new mixes, on folds that hold out whole mixes, on scaling learned from each fold's fit tests, and on an error that counts the choice. Each problem shows up only there. Together they would have told the plant to expect {% $fig.told %} MPa on new mixes, where nested cross-validation gives {% $fig.nested %} MPa.

---

Every problem let the job count on something it shouldn't: the test set, the mixes of held-out tests, their means and spreads, or the luck that picked the winner. Each one lowered an error the plant would have read, and none of them failed or warned.
