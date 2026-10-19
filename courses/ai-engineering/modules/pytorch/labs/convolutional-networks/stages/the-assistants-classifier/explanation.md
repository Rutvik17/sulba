The assistant's tests ran each part once, on a network just made. None of the problems changes a shape, probabilities of probabilities still sum to 1, and the loss still fell with all four problems in the code, so a loss that falls proves little.

---

Review a network's code by what each line does to its training: which parameters the optimizer holds, what the loss is given, what dtype each weight is kept in, and whether each layer is a module of its own. `parameters()` lists a shared parameter once, so counting the parameters against the design finds a module made once and used twice.
