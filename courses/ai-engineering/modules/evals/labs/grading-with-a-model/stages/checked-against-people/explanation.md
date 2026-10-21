People found {% $fig.dev_risky %} of the development replies and {% $fig.test_risky %} of the test replies say something their text doesn't. The grader's verdicts, at the threshold of {% $fig.default %} its two words suggest, and at {% $fig.chosen %}, the threshold the development set chose:

| Set | Threshold | Accuracy | Kappa | Called 1 |
| --- | --- | --- | --- | --- |
| Development | {% $fig.default %} | {% $fig.dev_default_accuracy %} | {% $fig.dev_default_kappa %} | {% $fig.dev_default_flagged %} |
| Development | {% $fig.chosen %} | {% $fig.dev_chosen_accuracy %} | {% $fig.dev_chosen_kappa %} | {% $fig.dev_chosen_flagged %} |
| Test | {% $fig.default %} | {% $fig.test_default_accuracy %} | {% $fig.test_default_kappa %} | {% $fig.test_default_flagged %} |
| Test | {% $fig.chosen %} | {% $fig.test_chosen_accuracy %} | {% $fig.test_chosen_kappa %} | {% $fig.test_chosen_flagged %} |

At {% $fig.default %}, the grader calls fewer replies ungrounded than people do. Its scores rank them well, with an AUC of {% $fig.dev_auc %} on the development set and {% $fig.test_auc %} on the test set, so a lower threshold calls about as many as people do and agrees with them far more. The threshold is chosen on the development set and reported on the test set, which it never saw: its kappa of {% $fig.test_chosen_kappa %} there is the one to quote. Chosen on the test set, a threshold would report the best kappa that set allows, not what the grader will do on the next.

Accuracy rewards a grader that calls everything ungrounded on a set where most replies are: kappa takes out the agreement chance alone would reach.
