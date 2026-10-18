A run's next step depends on more than the reader. SGD with momentum steps along a running sum of gradients: for each parameter `$\theta$`, a buffer `$b$` keeps a share `$\mu$` of itself, the momentum, and adds the gradient `$g$`, and the step moves `$\theta$` by the learning rate `$\gamma$` times the buffer.

```math
\begin{aligned}
b &\leftarrow \mu b + g \\
\theta &\leftarrow \theta - \gamma b
\end{aligned}
```

A run picked up without the buffers takes other steps from the first one on. The next epoch's order depends on the state of the loader's generator, {% $fig.generator %} bytes. And the run has to know how many epochs it had done, to train only the rest. So a checkpoint holds four things: the reader's state dict, which holds its buffers; the optimizer's, which holds its momentum buffers; the generator's state; and the count.

With all four put back, the arithmetic after a stop is the arithmetic the run would have done. On the same machine and the same PyTorch, with operations as deterministic as these on the CPU, it gives the same numbers to the last bit: a run stopped and picked up ends with exactly the weights of one that never stopped. The stop leaves no trace, so a run that stopped can be compared with runs that didn't.

`torch.load` reads a checkpoint by unpickling it, and a pickle can be made to run any code. Its default, `weights_only=True`, builds only what a checkpoint of state dicts needs and imports nothing, which narrows what a file can do as it loads, though PyTorch still warns never to load one from a source you don't trust. A checkpoint that pickles whole modules or optimizers needs `weights_only=False`, which gives that up.
