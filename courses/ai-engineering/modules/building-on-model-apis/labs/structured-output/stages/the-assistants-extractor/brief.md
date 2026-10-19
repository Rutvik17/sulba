The shop asked an assistant for the code that turns customers' emails into entries for its calendar. The assistant wrote `bookings.py`, whose `book` has the model fill in the shop's form with your `ask_for`, checks the date, and returns the entry. Its four tests all pass.

Review it as if the shop were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the shop will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- return an entry only for a date that exists and hasn't passed, and never for a Sunday, when the shop is closed;
- give each booking one time, on the hour or the half hour, from `09:00` to `16:30`;
- give the calendar the form's keys and no others;
- raise `NotBooked` for an email it can't book, so that a person answers it.
