```python
def match_probability(pairs, temperature=1.0, shift=0.0):
    yes = pairs["yes"].to_numpy() / temperature + shift
    no = pairs["no"].to_numpy() / temperature
    return softmax(np.column_stack([yes, no]))[:, 0]


def calibrate(pairs):
    margin = (pairs["yes"] - pairs["no"]).to_numpy()
    exact = (pairs["label"] == "E").to_numpy()

    def log_loss(parameters):
        slope, shift = parameters
        logs = log_softmax(
            np.column_stack([margin * slope + shift, np.zeros(len(margin))])
        )
        return -np.mean(np.where(exact, logs[:, 0], logs[:, 1]))

    slope, shift = minimize(log_loss, x0=[1.0, 0.0]).x
    return 1 / slope, shift
```

`match_probability` is a softmax over two logits alone, Yes's and No's, each divided by the temperature, with the shift added to Yes's: the judge's answer when it may say only Yes or No. Fitting it is a logistic regression on the margin, with `$1/T$` as its slope and `$b$` as its intercept. The log loss is convex in the slope and the shift, so `minimize` finds the one best fit from any start; in `$T$` itself it isn't.

Fitted on the {% $fig.validation %} validation pairs, the temperature is {% $fig.temperature %} and the shift {% $fig.shift %}: the judge is far too sure of itself, and leans to Yes. On the {% $fig.test %} test pairs, which hold {% $fig.test_exact %} exact matches:

| Probabilities | Brier score | They add up to |
| --- | --- | --- |
| The judge's own | {% $fig.raw_brier %} | {% $fig.raw_sum %} |
| Calibrated | {% $fig.cal_brier %} | {% $fig.cal_sum %} |
| A temperature alone | {% $fig.t_brier %} | {% $fig.t_sum %} |
| The validation share for every pair | {% $fig.share_brier %} | {% $fig.share_sum %} |

A temperature alone, fitted without the shift, makes the judge less sure but leaves it leaning to Yes, so its probabilities add up to far more exact matches than there are. Calibrated, the probabilities of the test pairs run from {% $fig.lowest %} to {% $fig.highest %}. They mean about what they say, and what they say is that the judge knows a little about which products match: its probability is a reason to look at a pair, not an answer.
