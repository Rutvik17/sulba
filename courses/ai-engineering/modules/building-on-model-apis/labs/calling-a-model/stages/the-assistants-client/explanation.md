Each problem passed the assistant's tests because each test checked something next to it. The tests showed that an answer came back, not what a customer reads when none does; that the conversation grew, not who said what in it; and that each prompt fit in the window, not that the reply did too.

A customer sees only the assistant's words, so everything else that comes back from the model is for the shop: an error's message goes to the shop's logs, and a reply that didn't finish with `stop` goes nowhere. A reply cut off at `length` and a reply that calls a tool both look like text a customer could be shown until the reason is checked.

The roles are the conversation's structure. The model reads turns of `user` and `assistant`, which its template writes with each message's role, so a reply sent back as the customer's tells the model the customer said it.

The window holds the prompt and the reply together, which is why `fit` takes the reply's tokens. Without them, a long conversation grows until its prompt nearly fills the window, and the replies are cut off at whatever room is left.
