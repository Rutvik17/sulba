Ship the office's optimizer. `make_optimizer(params)` returns one of your optimizers, with the settings it trains best with, made for a network's arrays. The office trains with it on a budget:

```
for each step of the budget:
    rows = the next batch of training digits, in an order shuffled for each pass over them
    optimizer.step(the network's gradients on those rows)
```

The network is the office's own: {% $fig.budget %} steps, in batches of {% $fig.batch %}, through a hidden layer of {% $fig.hidden %} ReLUs, started as `torch.nn.Linear` starts. Choose the optimizer and its settings on the {% $fig.validation %} validation digits, which come from the same people as the {% $fig.training %} training digits. The office reads people it has never seen, and so do the checks: they read the {% $fig.test %} test digits, written by others.

Training runs stop, and the office takes them up from where they stopped. The optimizer must save everything its next steps depend on and load it into a new optimizer made for a copy of the weights, so that the run goes on as if it never stopped:

```
make_optimizer(params) -> an optimizer with step(grads), state_dict() and load_state_dict(state)
```

There are no hints. The tests are hidden: you see which pass, but not their inputs. Two more checks decide whether it ships.
