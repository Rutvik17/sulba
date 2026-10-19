An online shop sorts the photos in its catalogue into {% $fig.kinds %} kinds of article, from T-shirts and bags to ankle boots. Each photo is {% $fig.side %} by {% $fig.side %} pixels, in grey, and a convolutional network is to sort them. Such a network is built from convolutions and pooling, so those come first: in `conv.py`, write PyTorch's convolution and max pooling by hand, without its own convolution, `F.unfold` or pooling.

- `conv2d(x, weight, bias=None, stride=1, padding=0, dilation=1, groups=1)`, which gives what `F.conv2d` gives. `x` is a batch of shape `(N, C, H, W)`, and `weight` holds `O` filters of shape `(C / groups, kh, kw)`. `padding` adds that many zeros on each side, `stride` is the step between the positions a filter takes, and `dilation` is the step between the pixels it covers. Each is an int, or a pair for the height and the width. With `groups`, the channels split into that many groups in order, and each filter covers one group's channels, the filters split among the groups in order too.
- `max_pool2d(x, kernel, stride=None)`, which gives what `F.max_pool2d` gives without padding: the largest pixel of each `kernel` by `kernel` window, the windows `stride` apart, or `kernel` apart if `stride` is `None`. `kernel` and `stride` are each an int, or a pair for the height and the width. Each window's gradient goes to its first largest pixel, reading row by row, as PyTorch's does.

At each position, a filter multiplies each pixel it covers by its weight there, adds up the products over its channels, and adds its bias. For a padded photo with `$C$` channels and a filter `$w$` of `$k$` by `$k$`, with stride `$s$` and dilation `$d$`, the output at row `$r$` and column `$c$` is:

```math
y_{r,c} = b + \sum_{m=0}^{C-1} \sum_{i=0}^{k-1} \sum_{j=0}^{k-1} w_{m,i,j} \, x_{m,\, rs+id,\, cs+jd}
```

```
conv2d(x, weight, bias=None, stride=1, padding=0, dilation=1, groups=1) -> (N, O, H_out, W_out)
max_pool2d(x, kernel, stride=None) -> (N, C, H_out, W_out)
```
