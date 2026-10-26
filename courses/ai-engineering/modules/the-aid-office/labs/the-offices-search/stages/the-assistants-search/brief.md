Before you started, the office asked an assistant for the search its own assistant will call. The assistant wrote `finder.py`: `embedding`, a question's vector from the model; `answerable`, whether a passage is close enough to the vector to answer the question; `pages`, the best pages, in one query; and `find`, which puts them together, and searches by words alone when the model can't embed the question. Its three tests all pass.

Review it as if the office were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office's assistant will call it, on the office's passages and their recorded vectors. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- find pages by any of a question's words when the model is down;
- give the best pages, best first;
- keep the office's own questions;
- search by words whenever the model can't give a vector.
