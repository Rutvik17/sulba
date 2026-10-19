Within the budget, each model reads as many tokens as its cost a token allows:

| Width | Blocks | Context | Parameters | Tokens within the budget | Tokens for each parameter |
| --- | --- | --- | --- | --- | --- |
| {% $fig.width_0 %} | {% $fig.layers_0 %} | {% $fig.context_0 %} | {% $fig.params_0 %} | {% $fig.read_0 %} | {% $fig.each_0 %} |
| {% $fig.width_1 %} | {% $fig.layers_1 %} | {% $fig.context_1 %} | {% $fig.params_1 %} | {% $fig.read_1 %} | {% $fig.each_1 %} |
| {% $fig.width_2 %} | {% $fig.layers_2 %} | {% $fig.context_2 %} | {% $fig.params_2 %} | {% $fig.read_2 %} | {% $fig.each_2 %} |
| {% $fig.width_3 %} | {% $fig.layers_3 %} | {% $fig.context_3 %} | {% $fig.params_3 %} | {% $fig.read_3 %} | {% $fig.each_3 %} |

A larger model can learn more from each token, and a smaller one reads more tokens. Hoffmann and colleagues trained over {% $fig.chinchilla_trained %} language models to find the balance, and found that for a budget of compute, the model's size and its training tokens should grow together: for every doubling of the model, double the tokens. Their Chinchilla, {% $fig.chinchilla %} parameters trained on {% $fig.chinchilla_tokens %} tokens, {% $fig.chinchilla_each %} for each parameter, did better than Gopher, {% $fig.gopher %} parameters, trained with the same compute.

The model `make()` gave at first reads fewer tokens than it has parameters within this budget. A shorter context costs less too: attention's part of a token's cost grows with the context, and a story's tokens past the context are read without its start.
