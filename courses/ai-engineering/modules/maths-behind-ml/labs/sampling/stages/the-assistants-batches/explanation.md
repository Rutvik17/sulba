The assistant's tests checked one epoch's shape: no batch over `size`, row numbers in range, the same batches from the same seed. An epoch drawn with replacement passes all three, and so does one that leaves out the short batch, since every batch it keeps has `size` rows. The average was tested on a full batch, where dividing by `size` and by the batch's length give the same. No test drew two epochs, so none saw that they were the same.

---

A sampler's promises are about many draws: each record once an epoch, a new order each epoch, the same order for the same seed and epoch. Each one is a test. Draw several epochs and compare them, count how often each record turns up, and test the short batch on its own, where the size asked for and the size drawn differ.
