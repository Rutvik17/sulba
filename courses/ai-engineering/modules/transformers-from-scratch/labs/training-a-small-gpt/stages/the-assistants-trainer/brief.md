The app's team asked an assistant for a trainer of its own: the stories as one stream of tokens, batches from random places in it, GPT-3's learning rate, and a way to write stories longer than the model's context. The assistant wrote `trainer.py`, which uses your tokenizer and your GPT. Its four tests all pass.

Review it as if the app were about to train its model with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the app will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- put the separator after each story, so the model learns where stories end;
- take each window's targets one token on from its inputs;
- raise the learning rate over the warm-up, then lower it along a cosine to a tenth of the peak;
- give the model a story's latest tokens once the story is longer than the context.
