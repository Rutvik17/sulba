The clinic will train its network with weight decay: the loss adds `l2 / 2` times the sum of the squared weights, which keeps the weights small. The clinic asked an assistant for the loss and its gradient, and the assistant wrote `network.py`. Its four tests all pass, one of them a numerical check of the gradient.

Review it as if the clinic were about to train with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way training will use it. A run shows how many pass. You see which ones when you finish the review.

The clinic's request:

- The loss: stage 3's mean log loss, plus `l2 / 2` times the sum of the squares of the weights in `W1` and `w2`. The biases aren't decayed.
- The loss's gradient with respect to `W1`, `b1`, `w2` and `b2`, right at any weights training reaches.
- A finite loss for any weights, however confident the network becomes.
