The help desk asked an assistant for its search before you started. The assistant wrote `search.py`, whose `Search` embeds the passages with your `Cache`, keeps each one cut to `NUMBERS` numbers of a byte each, and finds the best passages for each question. Its three tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- embed the passages as passages, and the questions as questions;
- cut each vector as the model's card does;
- give each passage its own id;
- put each question's best passage first.
