The assistant's tests looked at the model at the moment it was made: the shape of its logits, its causal mask, and its output layer's numbers before any training. Every problem here passes them. Each shows only in what the model does next: a block run on its own, the two tables after a step of training, a story as long as the context, and a model {% $fig.deep %} blocks deep.

A tied output layer is one parameter held by two modules, so `parameters()` counts it once and every gradient step moves both. A copy is a second parameter that starts equal and drifts.
