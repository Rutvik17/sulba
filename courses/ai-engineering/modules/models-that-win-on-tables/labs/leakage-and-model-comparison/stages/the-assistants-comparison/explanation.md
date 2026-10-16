The assistant's tests checked that a pair joins a job and an education, that the shares lie between 0 and 1, that a model gets an AUC on every fold, and that an interval holds the mean and widens with the confidence. None flipped a held-out call's answer to see whether its shares moved, compared a model with a copy of itself, or worked out a standard error or an interval by hand.

---

With the four problems fixed, the shares add nothing: the baseline's mean AUC is {% $fig.base_fixed %} with them and {% $fig.base_bare %} without, and no model's interval leaves 0 out. A column can carry no information about new calls and still lift every score, when it is learnt from the answers it is scored against.
