The app's team asked an assistant for the whole model in one file, with the attention and the MLP inside each block, and an output layer that starts from the token embeddings, as GPT-2's does. The assistant wrote `gpt.py`, with `AppGPT(vocab, context, width, layers, heads)`. Its four tests all pass.

Review it as if the app were about to train it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the app will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- add each part's output to the residual stream, reading it through a layer normalization, as GPT-2's blocks do;
- read and write tokens with one table of vectors;
- give a story's first token the first position, and read stories as long as the context;
- start the residual stream at the same size however many blocks the model has.
