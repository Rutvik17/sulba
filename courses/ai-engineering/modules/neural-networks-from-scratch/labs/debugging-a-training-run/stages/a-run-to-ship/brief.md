Ship the office's training run. `train_office(seed, batches=1000, loss_and_grads=loss_and_grads)` trains the office's network from `np.random.default_rng(seed)` on `batches` batches of training digits, and returns it with the run's report:

```
{"lr": its learning rate, "batch": the digits in each batch,
 "batches": the batches it trained on, "validation": the share of validation digits it reads}
```

The office trains on a budget of {% $fig.budget %} batches of at most {% $fig.batch %} digits. Choose the settings on the {% $fig.validation %} validation digits with your checks from stages 1 to 3, the range test above all, and train with your `train` from stage 4.

The checks run the office's run once, through a `loss_and_grads` of their own that counts its batches. Then they read the {% $fig.test %} test digits, written by people none of the {% $fig.training %} training digits came from, and measure what the report says. A report has to hold: the same seed must train the same network, and the network must read what the report says it reads.
