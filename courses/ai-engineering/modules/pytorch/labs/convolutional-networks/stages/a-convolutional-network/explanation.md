The shop's network takes a photo through two convolutions, each pooled to half its side, then gives its features a logit for each kind:

| Layer | Output | Parameters | Multiply-adds |
| --- | --- | --- | --- |
| `Conv2d(1, 16, 3, padding=1)` | {% $fig.out0 %} | {% $fig.params0 %} | {% $fig.macs0 %} |
| `MaxPool2d(2)` | {% $fig.out2 %} | | |
| `Conv2d(16, 32, 3, padding=1)` | {% $fig.out3 %} | {% $fig.params3 %} | {% $fig.macs3 %} |
| `MaxPool2d(2)` | {% $fig.out5 %} | | |
| `Linear(32 * 7 * 7, 10)` | {% $fig.out7 %} | {% $fig.params7 %} | {% $fig.macs7 %} |

Of its {% $fig.params %} parameters, the convolutions hold {% $fig.conv_params %}, and of its {% $fig.macs %} multiply-adds a photo, they do {% $fig.conv_macs %}: each of their weights works at every position. The shop's current classifier, a perceptron with one hidden layer of {% $fig.hidden %} units between the pixels and the kinds, holds {% $fig.perceptron %} parameters and does {% $fig.perceptron_macs %} multiply-adds a photo. The network holds {% $fig.fewer %} times fewer parameters than the perceptron, and does {% $fig.more %} times as many multiply-adds.

Code that runs on any device takes the device as an argument and puts everything there. `net.to(device)` moves a network's parameters and buffers in place, while `X.to(device)` gives the batch on the device, a copy unless it's there already, and leaves `X` where it was. An operation needs all its tensors on one device, and a tensor made without `device=` is made on the CPU. `torch.accelerator.current_accelerator(check_available=True)` gives the machine's accelerator, such as a GPU, or `None` where there is none. Each `.item()` and each copy to the CPU makes the CPU wait for the device to finish its queue, which is why `train` reads its losses once an epoch.

On the `meta` device, a tensor has a shape and a dtype but no data. A forward pass there works out every shape and computes nothing, so it counts a network's work without doing it, and code that makes a tensor on the CPU by mistake fails at once.

bfloat16 keeps float32's {% $fig.exponent %} bits of exponent and {% $fig.fraction %} of its {% $fig.f32_fraction %} bits of fraction, so it has float32's range at a precision of about {% $fig.digits %} significant digits:

| Format | Largest | Smallest normal | Step after 1 |
| --- | --- | --- | --- |
| float32 | `$\fig{f32_max}$` | `$\fig{f32_tiny}$` | `$\fig{f32_eps}$` |
| bfloat16 | `$\fig{bf16_max}$` | `$\fig{bf16_tiny}$` | `$\fig{bf16_eps}$` |
| float16 | `$\fig{f16_max}$` | `$\fig{f16_tiny}$` | `$\fig{f16_eps}$` |

Under `torch.autocast`, the operations PyTorch lists for it run in bfloat16, convolutions, linear layers and matrix multiplies among them, and those that need float32 run in float32, cross-entropy among them. The weights stay float32: autocast casts them for each operation, and their gradients come back in float32. Cast the weights themselves to bfloat16, and a weight of {% $fig.weight %} would be stored as {% $fig.stored %} and move in steps of {% $fig.step %}: an update smaller than {% $fig.lost %} would leave it where it was. In bfloat16, small gradients keep float32's range. In float16, a gradient below {% $fig.f16_small %} loses precision, and one smaller still rounds to 0, which is why float16 training scales its loss up and bfloat16 training doesn't.

The photos lose precision too. A pixel's byte divided by 255 is off by up to {% $fig.pixel_error %} of its value in bfloat16, where in float32 it's off by up to `$\fig{f32_pixel}$` of it.

Whether bfloat16 trains faster depends on the chip. GPUs whose tensor cores take bfloat16 multiply matrices in it far faster than in float32, while a CPU without bfloat16 instructions can multiply them more slowly. Time `train` both ways on your machine.
