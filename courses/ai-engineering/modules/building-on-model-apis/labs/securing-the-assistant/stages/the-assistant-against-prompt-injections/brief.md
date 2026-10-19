The shop's chat window is ready for the assistant. It sends each message a signed-in customer types, shows each reply's HTML, and shows a button for each action waiting for the customer, which sends the action's id back when pressed. This stage writes the assistant's side, and ships it the way an attacker would try it: against a model that does whatever any text it reads tells it to.

In `chat.py`, write `Chat(client, db, actions, customer, clock)`, one customer's conversation:

- `send(message)`: the `Reply` to the customer's next message, its HTML from your `render` and the actions waiting for the customer. Send the conversation so far, with `TOOLS` from `shop.py` and `CANCEL`, and run each call the model makes: lookups with your `Tools`, and `cancel_booking` by proposing it with your `Actions`. A tool result tells the model what's waiting for the customer, and never an action's id.
- `press(id)`: the `Reply` when the customer presses an action's button: what `confirm` says, or why it refused.

Hold it to these limits:

- a message of more than `LONGEST` characters gets `TOO_LONG`, with no request;
- each request asks for at most `REPLY_TOKENS`, and a message takes at most `ROUNDS` requests;
- a customer's requests can use `DAILY_TOKENS` a day by `clock`, prompts and replies, counted from each reply's `usage`, and after that get `SPENT`, with no request, until the next day.

When the API answers with an error, the connection drops or times out, or a reply is cut off at its limit, the customer gets `SORRY`. When the shop's records can't be read, the model gets an error that says only that.

```
Chat(client, db, actions, customer, clock).send(message) -> Reply
Chat(client, db, actions, customer, clock).press(id) -> Reply
```

Two tests run on every attempt. Then six checks run before the code ships.
