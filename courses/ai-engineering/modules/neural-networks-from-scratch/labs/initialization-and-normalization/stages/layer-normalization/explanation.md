The two layers normalize along different axes of the same batch: batch normalization each feature over the samples, layer normalization each sample over the features. That one change removes everything that made batch normalization depend on its batch. A sample's output is a function of that sample alone, so there's nothing to estimate for evaluation, and a batch of one is as good as any other.

Its cost is what it normalizes away. Within each sample, the features' mean is set to 0 and their spread to 1, whatever they were, so how large a sample's signal was across its features is lost, and only the weight and the bias can scale and shift it again. Which of the two trains a network better is a question for its validation digits, and the last stage asks it.

A sample whose features are all the same has a variance of 0, and `$\epsilon$` keeps the division finite: `$\hat{x}$` is 0, and the output is the bias.
