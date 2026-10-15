The assistant's tests looked the records themselves up as new samples, checked the shapes, and compared the shares over the whole batch, so they passed. A batch of all the records has the records' own mean and standard deviation, so scaling it by itself happened to come out right. The clinic's batches aren't the records: they are new samples, in any number, with measurements that may not vary, in arrays the system keeps using, and each sample needs its own share.

---

Each problem kept the output's shape and range: {% $fig.k %} records for each sample, distances of 0 or more, shares between 0 and 1. Only tests that use the search as the clinic will, with other batches and other data, and with the arrays checked afterwards, show them.
