A contact the desk does saves the office an agent's time on it, and one it doesn't do goes to an agent as before. The office's figures are in `worth.py`: an agent's minutes on each kind of contact, and what a minute of an agent costs it, {% $fig.agent %}, or {% $fig.hourly %} an hour.

| Kind | An agent's minutes |
| --- | --- |
| Questions | {% $fig.question_minutes %} |
| Cases | {% $fig.case_minutes %} |
| Callbacks | {% $fig.callback_minutes %} |
| New tickets | {% $fig.new_minutes %} |
| Vague requests | {% $fig.vague_minutes %} |

The desk costs the office its machine, {% $fig.host %} for each hour it spends on contacts, and the team's support, {% $fig.support %} a month. The pilot's price, from the quote, is {% $fig.price %}.

In `worth.py`, write:

- `seconds(runs, variant)`: each kind's mean seconds a trial, from `runs.csv`'s `seconds`.
- `monthly(shares, durations, ...)`: the dollars a month the desk saves the office, net of its machine and its support, as an `Estimate`, with `low` and `high` the net less and plus `$z$` standard errors.
- `payback(price, net)`: the months the pilot takes to pay for itself, `price` over the net a month, with `low` from the net's `high` and `high` from its `low`. A net of 0 or less never pays: its months are `math.inf`.

With `$V_k$` each kind's contacts, `$m_k$` an agent's minutes, `$p_k$` and `$s_k$` its share done and standard error, `$t_k$` its mean seconds, `$a$` an agent's minute and `$h$` the machine's hour, the net and its standard error are:

```math
\begin{aligned}
\text{net} &= a \sum_k V_k m_k p_k - \frac{h}{3600} \sum_k V_k t_k - \text{support} \\
\text{error} &= a \sqrt{\sum_k (V_k m_k s_k)^2}
\end{aligned}
```

For the office, the desk saves {% $fig.net %} a month net, from {% $fig.net_low %} to {% $fig.net_high %}, and the pilot pays for itself in {% $fig.months %} months, from {% $fig.months_low %} to {% $fig.months_high %}.

```
seconds(runs, variant) -> dict[str, float]
monthly(shares, durations, volumes=OFFICE, minutes=MINUTES, agent=AGENT,
        host=HOST, support=SUPPORT, confidence=0.95) -> Estimate
payback(price, net) -> Estimate
```
