Before you started, the IT team asked an assistant for the advisers' schedule, which the desk's Java service will book callbacks into. The assistant wrote `Schedule.java`: it opens a service's days for callbacks, each with eight slots an hour apart, slot 0 at 09:00 and slot 7 at 16:00, books a ticket's callback into a free slot, and gives the bookings and the open days. Its five tests all pass.

Review it as if the desk were about to book callers with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the desk will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- find a ticket's bookings by any id with the same text, such as one read from a request's JSON;
- book any free slots on one day, each slot once;
- keep its bookings in the order they were made, whatever a caller does with the list it gives;
- give the open days in the calendar's order, however they were opened.
