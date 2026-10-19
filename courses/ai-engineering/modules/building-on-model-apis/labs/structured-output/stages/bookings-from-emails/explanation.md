The form and the code split the work. The form holds what the model writes: the reply's shape and keys, the bikes and services the shop knows, and every time a booking can start, so a reply that breaks them goes back to the model with its errors. The code holds what depends on the calendar: whether the date exists, whether it has passed, whether the shop is open that day. Those come from what the customer asked for, which the model can't change, so they go to a person.

`null` is the form's way to say no. Held to a form with no such way, a model fills it in whatever the email says, and an email asking whether the shop sells inner tubes becomes a booking for a puncture.

Every object in the form lists its keys in `required` and refuses others, as OpenAI's strict mode asks, and a field that may be empty has `null` among its types. The server can then hold a reply to the form, and the form's errors can say exactly what a reply got wrong.
