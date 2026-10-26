A travel company sells train tickets and hotel rooms in {% $fig.countries %} countries. It wants an assistant on its site that plans a trip from a request such as "a few days in the mountains by train, on a budget", finds the trains and hotels through the company's booking systems, and gives the customer a plan they can book at once. About {% $fig.visitors %} visitors a day ask it for a plan.

Design it. Take these as given:

- a plan needs about {% $fig.searches %} searches of the booking systems, and each takes about {% $fig.search_s %} seconds;
- the searches come in {% $fig.rounds %} rounds: the trains first, then the hotels near the stations they reach;
- a hotel room can be held for {% $fig.hold_minutes %} minutes before it's booked.
