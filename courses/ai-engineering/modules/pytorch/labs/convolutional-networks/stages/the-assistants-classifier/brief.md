The shop wants a deeper classifier and asked an assistant for it. The assistant wrote `classifier.py`, and its three tests all pass.

Review it as if the shop were about to train with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the shop will use it. A run shows how many pass. You see which ones when you finish the review.

The shop's request:

- `Block(inputs, outputs)`: a 3 by 3 convolution with padding 1 and no bias, a batch norm, then a ReLU.
- `Classifier()`: `stem`, a `Block(1, 16)`, then a 2 by 2 max pool, then `blocks`, two `Block(16, 16)`, each with weights of its own. Then a max pool again, and `head`, which flattens the features and gives a logit for each kind.
- `fit(net, images, labels, epochs, seed)`, which trains every layer of `net` by SGD with momentum, in an order seeded with `seed`, in bfloat16 under `torch.autocast`, its weights kept in float32. It returns each epoch's mean loss.
- `classify(net, photos)`, which gives each photo's kind and the probability of each kind, for the site to show, in evaluation mode.
