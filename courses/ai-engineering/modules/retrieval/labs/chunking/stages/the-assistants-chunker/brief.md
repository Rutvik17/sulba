The help desk asked an assistant for the chunker it will run on new pages before you started. The assistant wrote `splitter.py`: `split`, a page's blocks joined in order until another would take a chunk past `most` words, with a block of more than `most` words cut into windows of `most` words; `windows`, which cuts a block; and `places`, each chunk's place in its page. Its three tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its pages, with chunks of at most 100 words. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- keep every word of a page, in order;
- keep every chunk to `most` words;
- give chunks that are the page's own text;
- give each chunk its own place in the page.
