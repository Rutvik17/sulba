The office's runs get stopped: a laptop restarts for an update, a machine is needed for something else. A run that saves a checkpoint after each epoch can go on from it, and the office wants one that then ends exactly as it would have without the stop. In `checkpoints.py`, write:

- `train_epoch(reader, optimizer, batches)`, one epoch in training mode: for each batch that `batches` deals, the gradients cleared, the batch's mean cross-entropy and its backward pass, and a step of the optimizer. It returns the epoch's mean loss over its digits.
- `save(path, reader, optimizer, batches, epochs)`, which saves at `path` all that a run needs to go on after `epochs` epochs.
- `resume(path, reader, optimizer, batches)`, which loads the run saved at `path` into the reader, the optimizer and the batches of a run just started, and returns how many epochs it had done.

The office trains with `torch.optim.SGD` at a learning rate of {% $fig.lr %} and a momentum of {% $fig.momentum %}, and its checkpoints load with `torch.load`'s defaults.

```
train_epoch(reader, optimizer, batches) -> mean loss
save(path, reader, optimizer, batches, epochs)
resume(path, reader, optimizer, batches) -> epochs done
```
