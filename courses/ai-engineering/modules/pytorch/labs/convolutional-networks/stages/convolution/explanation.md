Along each side, a kernel of `$k$` pixels with dilation `$d$` spans `$d(k-1)+1$` pixels, and it takes a position every `$s$` pixels across the padded photo. That gives the output's size, as PyTorch computes it for convolution and pooling alike:

```math
H_\text{out} = \left\lfloor \frac{H + 2p - d(k-1) - 1}{s} \right\rfloor + 1
```

On the shop's photos, `nn.Conv2d(1, 16, 3, padding=1)` keeps the {% $fig.side %} by {% $fig.side %} pixels. With `stride=2` too, its output is {% $fig.strided %} by {% $fig.strided %}. With `dilation=2` and no padding, each filter's weights spread over {% $fig.span %} pixels across, and its output is {% $fig.dilated %} by {% $fig.dilated %}.

PyTorch's convolution doesn't flip its filters, as convolution in mathematics does: it computes a cross-correlation. A network learns its filters either way.

A filter takes the same weights to every position, so a convolution's parameters don't grow with the photo. `nn.Conv2d(16, 32, 3, padding=1)` holds {% $fig.conv %} parameters, on a photo of any size. A dense layer between the same feature maps of a photo {% $fig.half %} by {% $fig.half %} would hold {% $fig.dense %}: a weight for each pair of an input and an output number, and a bias for each output. Sharing the weights also means that, with `stride=1`, a photo moved by a pixel gives the same outputs moved by a pixel, away from its edges, so a filter that finds a collar finds it anywhere.

With `groups=g`, each filter covers `$C/g$` channels, so the layer holds `$1/g$` of the weights it would otherwise. `groups=C` gives each channel filters of its own, a depthwise convolution: `nn.Conv2d(16, 32, 3, groups=16)` holds {% $fig.depthwise %} parameters.

The tensor of windows, each output position's pixels side by side, is what libraries call im2col. With it, a convolution is one matrix multiply: at each position, its `$C k_h k_w$` pixels times each filter's weights.

Pooling keeps the largest pixel of each window. `nn.MaxPool2d(2)` halves each side and keeps a quarter of the numbers, and a feature found anywhere in a window counts the same. Its gradient goes only to the pixel it kept, since no other pixel of the window changes its output. When pixels tie, as pixels of the same grey often do, PyTorch's pooling sends it to the first, and so does `max` along a dimension.
