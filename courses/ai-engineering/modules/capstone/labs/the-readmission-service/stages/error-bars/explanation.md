Stage 2 held out one random draw of the stays. Drawn with each of {% $fig.seeds %} seeds, the same split gives held-out AUCs from {% $fig.held_low %} to {% $fig.held_high %}, and `SEED` 0's draw, {% $fig.held_out %}, is the highest of them. Nothing about the model changed between draws, only which stays fell in the test.

Cross-validation holds out every stay once. The five folds give AUCs of {% $fig.folds %}, and their mean, {% $fig.mean %}, leans on every stay rather than on one draw of them. Its standard error is {% $fig.error %}, so the mean give or take two standard errors runs from {% $fig.low %} to {% $fig.high %}. That is how the model's AUC should be reported, and how far apart two models must be before the difference means anything.

The error bar is a guide, not an exact measure. The five models share most of their training stays, so their AUCs aren't independent draws, which the formula takes them to be. It still shows the scale of the noise: the folds alone vary by more than the gap between many pairs of models.

From here on, the lab compares choices on these same five folds, with `SEED` fixed, so two models meet the same stays. A model is better only if it wins by more than the noise.
