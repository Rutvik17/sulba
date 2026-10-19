Of the file's {% $fig.tensors %} tensors, {% $fig.copied %} go into parameters, and {% $fig.transposed %} of those are turned around: the four linear layers' weights in each of the {% $fig.blocks %} blocks. A weight copied without `.T` fits only where a layer's inputs and outputs are the same size, as in the attention's output layer, and there it gives other numbers without an error, so only a check against GPT-2's own outputs finds it.

Given the app's opening line, "{% $fig.opening %}", GPT-2 took the likeliest token each time and wrote {% $fig.written %} more: "{% $fig.continuation %}" Taking the likeliest token every time often makes a model repeat itself, as it did here, so the training loop stage's `write` draws each token from its chances instead.

After "{% $fig.prompt %}", GPT-2's {% $fig.likeliest %} likeliest next tokens, with their chances, are {% $fig.shares %}.
