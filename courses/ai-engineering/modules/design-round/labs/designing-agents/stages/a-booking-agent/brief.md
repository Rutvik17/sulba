A chain of {% $fig.clinics %} physiotherapy clinics takes {% $fig.requests %} booking requests a day by chat: new appointments, moves and cancellations. Its booking system has an API to search free slots, and to book, move and cancel appointments. The chain wants an agent that makes the bookings itself, and passes to staff what it can't do.

Design it: the agent's tools, what it may do without asking, and how you'd know it's safe to let it act. Take these as given:

- a request takes the agent about {% $fig.steps %} model calls;
- each call is about {% $fig.call_in %} tokens in and {% $fig.call_out %} out;
- the model costs {% $fig.price_in %} per million tokens in and {% $fig.price_out %} per million out.
