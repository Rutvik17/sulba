A file cut short, or a file of kinds passed where photos belong, would otherwise give tensors of the wrong shape, or kinds out of step with their photos, and a network trains on either without an error. Checking the magic number and the data's size against the header costs a comparison each.

The sizes are big-endian: the training photos are counted in the bytes {% $fig.count_bytes %}, which say {% $fig.train %}. Read least significant byte first, the same bytes say {% $fig.little %}, and the check on the data's size refuses the file.

Kept as bytes, the training photos take {% $fig.bytes_mb %}. As `float32`, at 4 bytes a pixel, they take {% $fig.float_mb %}. Photos too many to hold as `float32` are kept as bytes, and each batch is converted as it's used.

A convolution takes its input as `(N, C, H, W)`. The shop's photos are grey, with one channel each, which `unsqueeze(1)` adds; a colour photo has three.

Each kind has {% $fig.per_train %} training photos and {% $fig.per_test %} test photos. A classifier that always gave one kind would be right on {% $fig.chance %} of the test photos: the floor any classifier must clear.
