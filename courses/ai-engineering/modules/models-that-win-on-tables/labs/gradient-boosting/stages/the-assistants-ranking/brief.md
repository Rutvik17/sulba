The call list was rebuilt with boosted trees by an assistant: `ranking.py`, whose `fit` trains XGBoost on the training calls and stops early on the validation calls, and whose `call_list` puts clients in the order to call them, the likeliest first, each with their chance of subscribing. Its four tests all pass.

Review it as if the list went out tomorrow: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the ranking must do:

- code each category as the training calls were coded, whichever clients it scores;
- stop early on the validation calls' log loss;
- give chances that add up to about the subscriptions, for the call centre to plan by;
- rank the clients by their chance of subscribing.
