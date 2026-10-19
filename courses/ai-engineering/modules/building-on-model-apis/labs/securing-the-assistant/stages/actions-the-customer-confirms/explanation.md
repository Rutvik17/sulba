A side effect the model can set off is one an attacker can set off, through anything the model reads. Asking the customer first leaves the decision with the one person the action is for, which OWASP's Top 10 for LLM Applications lists as requiring user approval for high-impact actions.

The approval has to come from outside the model. The button is the chat window's, and its id goes from the shop to the customer's browser and back. No tool takes the id, and no tool result holds it: a model that could confirm an action could be talked into confirming it.

Whoever has an action's id can try to confirm it, so the id is random, from `secrets`, which is made for this, and never built from the booking. It counts only for its own customer, and only for a while, so a proposal left waiting can't be confirmed long after the customer asked.

The cancellation checks the booking again, in the statement that changes it, because it may have changed since the question was asked.
