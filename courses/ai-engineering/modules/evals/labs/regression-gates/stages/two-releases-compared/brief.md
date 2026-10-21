Before a release replaces the current one, the help desk wants to know how its score moved: the candidate's score less the baseline's, with a margin of error. Both releases answered the same questions, and a question that one release finds hard, the other mostly does too. Taking each question's difference first takes out what the questions share; comparing the two scores alone leaves it in.

In `compare.py`, write:

- `Change`, a frozen dataclass of `change`, the candidate's score less the baseline's, and `margin`, how far its interval reaches each side at the confidence asked for.
- `paired(baseline, candidate, pages, confidence)`: the change from each question's difference, the candidate's mean less the baseline's, with its standard error taken from those differences, each page's together, as `standard_error` takes it.
- `unpaired(baseline, candidate, pages, confidence)`: the same change, with the standard error of each release's score, as `standard_error` gives it, added as if the two were independent.

```math
\begin{aligned}
d_i &= c_i - b_i \qquad \mathrm{SE}_{\text{paired}} = \mathrm{SE}(d) \\
\mathrm{SE}_{\text{unpaired}} &= \sqrt{\mathrm{SE}(b)^2 + \mathrm{SE}(c)^2}
\end{aligned}
```

`b_i` and `c_i` are question `i`'s means in the baseline and the candidate. `baseline` and `candidate` are arrays as `scores` gives them, on the same questions in the same order, and the margin is the standard error times the `z` that leaves `(1 - confidence) / 2` of the normal distribution above. The tests compare your standard errors with statsmodels'.

```
paired(baseline, candidate, pages, confidence) -> Change
unpaired(baseline, candidate, pages, confidence) -> Change
```
