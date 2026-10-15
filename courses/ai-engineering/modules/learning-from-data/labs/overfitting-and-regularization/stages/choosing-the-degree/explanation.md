Each degree's features include all of the last degree's, so least squares can always do at least as well on the training tests: it could give the new features no weight. The training error falls at every degree. The validation error, on mixes the fit never saw, falls and then climbs:

| Degree | Features | Training RMSE | Validation RMSE |
| --- | --- | --- | --- |
| 1 | {% $fig.count_1 %} | {% $fig.train_1 %} MPa | {% $fig.val_1 %} MPa |
| 2 | {% $fig.count_2 %} | {% $fig.train_2 %} MPa | {% $fig.val_2 %} MPa |
| 3 | {% $fig.count_3 %} | {% $fig.train_3 %} MPa | {% $fig.val_3 %} MPa |
| 4 | {% $fig.count_4 %} | {% $fig.train_4 %} MPa | {% $fig.val_4 %} MPa |

At degree 2, the model bends where the tests do, and its error on new mixes falls from {% $fig.val_1 %} to {% $fig.val_2 %} MPa. Past it, the extra weights fit the noise in the training tests instead: at degree 4 there are {% $fig.count_4 %} weights for {% $fig.train_tests %} training tests. A model that fits its training data much better than it predicts new data is overfitting.

The degree is chosen on the validation mixes: here, degree 2. It was chosen for its low validation error, so that error tends to flatter it. The test mixes stay unused until a model is chosen, and then give the honest error on new mixes.

The tests are split by mix, not one by one, because one mix is tested at several ages. Split one by one at random, {% $fig.twins %} of {% $fig.held %} held-out tests would have their mix among the training tests, and the validation error would measure how well the model remembers mixes, not how well it predicts new ones.

The chart fits each degree on fewer training mixes. With fewer to fit, overfitting starts at a lower degree.
