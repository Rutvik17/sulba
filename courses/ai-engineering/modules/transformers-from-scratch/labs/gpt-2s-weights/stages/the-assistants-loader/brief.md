The app's team asked an assistant for one module that gives the app GPT-2 and its tokenizer from the downloaded files. The assistant wrote `loader.py`, which uses your `tensors` and your GPT. Its four tests all pass.

Review it as if the app were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the app will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- copy every one of GPT-2 small's parameters from the file, leaving out only the causal masks;
- turn each linear layer's weight around, from GPT-2's (inputs, outputs) to `nn.Linear`'s (outputs, inputs);
- give a text's tokens as GPT-2's tokenizer does, with a separator only where the text has one;
- give back the text of any tokens, whatever characters they hold.
