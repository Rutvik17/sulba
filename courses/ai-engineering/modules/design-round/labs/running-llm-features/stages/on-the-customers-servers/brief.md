A hospital wants an assistant that answers its staff's questions from its policy documents, but nothing may leave its network: no hosted models and no outside calls. It offers {% $fig.servers %} servers, each with one GPU of {% $fig.gpu_gb %} GB, and expects at most {% $fig.peak %} staff to use the assistant at once.

Design what runs where, which model you'd choose and how you'd show it's good enough, and how it's kept up to date. Take these as given:

- the model you'd start from has {% $fig.params %} billion weights, stored in {% $fig.weight_bits %} bits each;
- it has {% $fig.layers %} layers, each keeping {% $fig.kv_heads %} key and value heads of {% $fig.head_dim %} numbers, cached in {% $fig.cache_bytes %} bytes each;
- a conversation with its passages can reach {% $fig.context %} tokens.
