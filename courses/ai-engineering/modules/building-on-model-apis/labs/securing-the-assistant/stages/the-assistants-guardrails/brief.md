The shop asked an assistant for the code that answers its signed-in customers. The assistant wrote `assistant.py`, whose `Assistant` offers the model your tools from `shop.py`, adds one for the times already booked on a day and one to cancel a booking, shows each reply through your `render`, and holds each customer to `DAILY_TOKENS` a day. Its three tests all pass.

Review it as if the shop were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the shop will use it, with a model that does whatever it reads, whether a customer or a review wrote it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- send the model nothing about any customer but the one signed in;
- take an action only when the customer presses its button;
- give the model only instructions any customer could read;
- count every token of a customer's conversations against their day.
