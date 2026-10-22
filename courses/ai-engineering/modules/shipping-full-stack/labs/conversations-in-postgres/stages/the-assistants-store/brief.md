Before you started, the help desk asked an assistant for a store of its own. The assistant wrote `desk_store.py`, whose `DeskStore` keeps the conversations in Postgres on your schema. Its four tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- read only the conversation whose id it's given, whatever the id holds;
- keep every message of turns kept at once in one conversation;
- keep a turn's messages and its usage together, or neither;
- give back every connection it takes from the pool.
