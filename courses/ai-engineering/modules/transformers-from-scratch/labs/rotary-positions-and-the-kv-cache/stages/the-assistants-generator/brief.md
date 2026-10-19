The app's team asked an assistant for the story writer the app will run: SmolLM2 with a KV cache, a token at a time. The assistant wrote `generator.py`, which uses your `Cache`, your `rotate` and your SmolLM2. Its three tests all pass.

Review it as if the app were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the app will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- give each new token the position after the tokens the cache holds;
- give each query head the key and value head of its group, as SmolLM2 was trained;
- let each new token read every cached token and the new ones up to itself;
- write each token after the last one read.
