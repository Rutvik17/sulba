Each of the assistant's tests checked something a wrong layer gets right too: a batch normalized to a mean of 0 and a variance of 1 in training, the weight and the bias, their gradients, the running mean, and a batch whose values were all the same. None of them ran in evaluation, read the running variance or the gradient with respect to the batch, or compared a result with PyTorch's.

---

The checks used the layers as a network does: in evaluation, with the estimates training left behind, through each training batch in turn, backward to the layer before, and on batches whose samples differ. A sample read alone is a quick test of both layers: in evaluation, each should give it the outputs it gets in any batch, and a layer that gives it its bias instead is normalizing over the batch.
