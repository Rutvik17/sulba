The assistant's tests checked that `encode` gives each category column a whole number, that `fit` keeps at most {% $fig.rounds %} rounds and the training calls' categories, and that the list holds every client once, from the highest chance down. None scored a client alone, asked which calls early stopping watched, added up the chances, or compared the list's chances with the model's.

---

A model's codes come from its training calls and its rounds from its validation calls, and both stay as they are for every client it scores after. XGBoost watches every set in `eval_set`, but stops early on the last. And when the chances themselves are used, as a call centre plans by them, a yes call and a no call weigh the same: a weight on the yes calls moves the chances up, away from the share who subscribe.
