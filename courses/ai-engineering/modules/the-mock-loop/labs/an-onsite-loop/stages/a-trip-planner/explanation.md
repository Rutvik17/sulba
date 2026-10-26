## What it must do

Turn a loose request into a trip the customer can book: trains and hotels that fit together, within their budget, with every price and time true when it's shown. Book all of it or none of it.

## Model and systems

The model turns the request into searches: where, when, how long, how much, which trains. It arranges what the searches find into a plan and writes the plan's words. Every price, time, seat and room comes from the booking systems, through tools, and the plan shows them from the search results, never from the model's text.

## Speed

{% $fig.searches %} searches at {% $fig.search_s %} seconds each take {% $fig.serial_s %} seconds one after another. The trains' searches don't depend on each other, nor do the hotels', so they run at once in {% $fig.rounds %} rounds, about {% $fig.parallel_s %} seconds. The plan streams meanwhile: the outline first, then each part as its results arrive.

## Checks

Code checks each plan before it's shown: the dates join up, each connection leaves enough time to change trains, every night has a room, and the total is within the budget. A plan that fails goes back to the model with the reason, once, and then the customer sees what doesn't fit.

## Booking

Booking holds every part, for at most {% $fig.hold_minutes %} minutes, then books them all. If any part fails, the holds are released and nothing is charged, so the customer never has half a trip.

## Measuring

A test set of requests, each with plans a travel agent judged, checks the limits each plan meets and the agent's ratings, on every change to the prompt, the tools or the model. After launch, the share of plans booked, and the parts customers change before booking, show where plans fall short.

## The follow-up questions

- **{% $fig.serial_s %} seconds of searching:** the searches run at once, about {% $fig.parallel_s %} seconds, and the plan streams as its parts arrive.
- **A hotel sells out:** the hold fails at booking, the holds already made are released, and the hotel is searched again for the nearest match, which the customer approves.
- **Good plans:** the test set with the agent's judgments before launch, then the share of plans booked.
