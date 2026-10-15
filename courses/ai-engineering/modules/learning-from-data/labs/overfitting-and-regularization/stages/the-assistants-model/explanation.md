The assistant's tests checked that `choose` returns a pair it tried, that the model gives a strength for each test, and that the error is a number of MPa, so they passed. The plant relies on more: on the model being the one you validated, on a choice made on mixes the fit never saw, and on an error measured on mixes the model hasn't seen. Each problem shows up only there, and together they flatter the model: the plant would have been told to expect {% $fig.told %} MPa on new mixes, where the honest estimate, from whole mixes held out, is {% $fig.mix_error %} MPa.

---

None of the four raised an error or printed a warning. A model that is fit or scored on the wrong tests still returns numbers, and they look better than they should, so the mistake hides behind a good result.
