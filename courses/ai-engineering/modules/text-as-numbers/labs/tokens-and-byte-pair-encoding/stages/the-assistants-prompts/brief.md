The shop asked an assistant for the code that builds its prompts. The assistant wrote `prompts.py`, with the shop's tokenizer in tiktoken and the special token `<|endoftext|>` as a separator after its vocabulary. `count` gives a text's tokens for the app to show beside each listing, `pack` puts as many titles as fit within the model's limit into a prompt, each followed by the separator, and `stream` gives the text of the model's reply as each of its tokens arrives. Its four tests all pass.

Review it as if it were about to go live in all three shops: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- count a text's tokens as the shop's tokenizer does, in any language;
- read every title as text, so that only the code puts special tokens in a prompt;
- keep each prompt within the limit, separators and all;
- show the reply's text as it arrives, without broken characters.
