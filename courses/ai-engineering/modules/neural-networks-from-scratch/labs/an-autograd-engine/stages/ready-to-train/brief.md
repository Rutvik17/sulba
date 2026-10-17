The office will train its networks with your engine, not with backward passes written by hand. Ship the engine ready for that.

First, the loss. Write `cross_entropy(logits, labels)`: the mean cross-entropy of a Tensor of logits, a row for each sample, against an array of labels, as PyTorch's `torch.nn.functional.cross_entropy` gives it. Make it from the engine's operations and return the Tensor they make, so that `backward` gives the logits their gradient with no backward pass written for it.

```
cross_entropy(logits, labels) -> a Tensor holding one number
loss.backward(), setting .grad on the logits and everything they were made from
```

Then depth. A network's graph grows with the network: residual networks have been trained {% $fig.resnet %} layers deep, and in your engine each layer is several steps. `backward` must work through a graph of any depth, deeper than Python lets a function call itself.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Two more checks decide whether it ships.
