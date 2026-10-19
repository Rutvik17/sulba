The shop asked an assistant for the code that answers customers' questions with the shop's tools. The assistant wrote `assistant.py`, whose `Assistant` offers the model `opening_hours` and `repair_price`, described with your `describe`, runs each call the model asks for, and sends the results back until the model answers. Its three tests all pass.

Review it as if the shop were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the shop will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- answer with the model's reply, or with `SORRY`, after no more than `ROUNDS` requests;
- run every call in a reply, and send each result back with its call's id;
- send a tool's error back as its result, for the model to read;
- run only the tools it offers the model.
