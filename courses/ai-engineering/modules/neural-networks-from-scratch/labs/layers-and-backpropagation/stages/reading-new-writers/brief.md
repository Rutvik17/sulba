Ship the office's reader. `train(pixels, digits, rng)` trains a network built from your layers on the training digits, with `rng` for all that's random, and returns `read`, a function that gives the digit it reads for each row of a batch of pixels.

```
train(pixels, digits, rng) -> read
read(pixels) -> an array of digits
```

Choose the network's size, the learning rate, the batches and how long it trains on the {% $fig.validation %} validation digits, which come from the same people as the {% $fig.training %} training digits. The office will use it on people it has never seen, and so do the checks: they read the {% $fig.test %} test digits, written by other people.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
