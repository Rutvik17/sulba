A grocery delivery app sells {% $fig.products %} products, whose prices and stock change every hour. It wants an assistant in the app that answers questions such as "what can I cook with what's in my basket?" and "do you have oat milk?", and adds what the customer chooses to their basket.

Design it: what comes from the model, what comes from the shop's systems, and what the customer confirms. Take these as given:

- {% $fig.customers %} customers use the assistant a day, each asking about {% $fig.turns %} questions;
- the catalogue's search answers in about {% $fig.search_ms %} milliseconds.
