The test set has its own mix of kinds, a third of its trials questions. The office's chat takes {% $fig.contacts %} contacts a month, in `mix.py`'s `OFFICE`:

| Kind | Contacts a month |
| --- | --- |
| Questions | {% $fig.question_contacts %} |
| Cases | {% $fig.case_contacts %} |
| Callbacks | {% $fig.callback_contacts %} |
| New tickets | {% $fig.new_contacts %} |
| Vague requests | {% $fig.vague_contacts %} |

In `mix.py`, write `weighted(shares, volumes, confidence=0.95)`, the share of the contacts the desk would do, as an `Estimate`. With `$w_k$` each kind's share of the contacts, and `$p_k$` and `$s_k$` its share done and standard error from your `by_kind`, the kinds' tasks being separate:

```math
p = \sum_k w_k\, p_k, \qquad s = \sqrt{\sum_k w_k^2\, s_k^2}
```

`low` and `high` are `$p$` less and plus `$z$` standard errors, `$z$` the normal distribution's quantile for the confidence, kept within 0 and 1. A kind in `volumes` without a share, or no contacts at all, raises `ValueError`.

For the office, the desk would do {% $fig.office %} of the contacts, from {% $fig.office_low %} to {% $fig.office_high %}.

```
weighted(shares, volumes, confidence=0.95) -> Estimate
```
