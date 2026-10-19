The shop sorts its photos with a perceptron with one hidden layer of {% $fig.hidden %} units, trained for {% $fig.epochs %} epochs by SGD on a one-cycle schedule, in batches of {% $fig.batch %} with a peak learning rate of {% $fig.perceptron_peak %}. It reads {% $fig.perceptron %} of the test photos right. It wants a convolutional network in its place that reads at least {% $fig.target %} of them, within its budget: at most {% $fig.budget %} multiply-adds a photo, and {% $fig.epochs %} epochs of training. In `shop.py`, write:

- `make()`, the shop's classifier, untrained.
- `fit(net, images, labels, seed)`, which trains `net` on the photos `images` and their kinds `labels`, with every order and every chance in its training decided by `seed`, and returns it, ready to classify photos.

The network and its training are yours to design: its layers, its optimizer, its schedule and its batches. Your `multiply_adds` from stage 3 counts what a network costs as the shop does.

```
make() -> network
fit(net, images, labels, seed) -> net, trained
```
