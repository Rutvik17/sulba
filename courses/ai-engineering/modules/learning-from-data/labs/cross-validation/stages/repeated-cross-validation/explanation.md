A shuffle of the folds is itself a draw. Over {% $fig.seeds %} seeds, one five-fold cross-validation chose degree {% $fig.chosen_degree %} with `$\lambda = \fig{chosen_penalty}$` for {% $fig.one_chose %} of them. Averaging each pair's error over several shuffles evens out the luck of any one:

| Shuffles averaged | Chose degree {% $fig.chosen_degree %}, `$\lambda = \fig{chosen_penalty}$` |
| --- | --- |
| One | {% $fig.one_chose %} of {% $fig.one_sets %} |
| Two | {% $fig.two_chose %} of {% $fig.two_sets %} |
| Three | {% $fig.three_chose %} of {% $fig.three_sets %} |
| Five | {% $fig.five_chose %} of {% $fig.five_sets %} |

The sets don't overlap: the {% $fig.seeds %} seeds are split into sets of one, two, three or five.

Each shuffle costs another whole cross-validation: two shuffles fit {% $fig.two_fits %} models where one fits {% $fig.cv_fits %}. The model the job ships, fit on every record, has an RMSE of {% $fig.test %} MPa on the test set, used once, after the choice.

Repeating steadies what depends on the shuffle, but it can't add records. Every shuffle deals the same {% $fig.records %} tests, so the average still carries the luck of which mixes the plant happened to test.
