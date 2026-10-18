Ship the office's training run. `run(path, train, validation, epochs=15, seed=0)` trains the office's reader and returns it with the state it had after the epoch with the lowest loss on the validation digits, in evaluation mode. It saves the run at `path`, a `pathlib.Path`, after each epoch and, run again, goes on from there and ends as a run that never stopped would have, even one stopped partway through saving.

The office trains as in stage 3: `torch.manual_seed(seed)`, then a reader from your `Reader` with the training digits' pixels, `torch.optim.SGD` at a learning rate of {% $fig.lr %} and a momentum of {% $fig.momentum %}, and your `batches(train, seed)`. Each epoch is your `train_epoch`, then the validation loss from your `evaluate`. Of two epochs with the same validation loss, it keeps the first.

```
run(path, train, validation, epochs=15, seed=0) -> reader
```

There are no hints. The tests are hidden: you see which pass, but not their inputs. Five more checks decide whether it ships.
