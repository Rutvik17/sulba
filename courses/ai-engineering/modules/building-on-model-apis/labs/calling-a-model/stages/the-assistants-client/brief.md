The shop asked an assistant for the code that will hold each customer's conversation with the model. The assistant wrote `client.py`, whose `Assistant` keeps the conversation, fits it to the model's window with your `fit`, and asks with your `ask`. Its three tests all pass.

Review it as if the shop were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the shop will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- answer with the model's reply, or with `SORRY` when there's none to give a customer;
- never show a customer a reply the model didn't finish;
- send the model's earlier replies back as the assistant's;
- leave room in the window for the reply.
