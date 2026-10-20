The help desk asked an assistant for its search page's queries before you started. The assistant wrote `queries.py`: `search`, the nearest passages to a question with their similarity; `search_in`, a service's nearest passages; and `similar`, the passages most like the one a reader has open. Its three tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the search page will use it, on the passages' table with your index. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- search through the index;
- send a service's name to Postgres apart from the query;
- give a service's passages nearest first;
- give the passages most like a passage first.
