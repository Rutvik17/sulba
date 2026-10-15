def worker_batches(n, size, workers, rank, epoch, seed):
    """The batches worker rank of workers trains on in epoch: its turns through one order of
    the row numbers 0 to n - 1, cut into batches of size rows."""
    raise NotImplementedError
