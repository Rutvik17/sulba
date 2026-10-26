## What it must do

Book, move and cancel appointments for the patient in the chat, and never for anyone else, with no booking the patient didn't agree to. When it can't, it passes the request to staff with what it found, rather than guessing.

## The tools

Each tool does one thing, and the booking system checks it:

- `find_slots(clinic, therapist, from, to)`: free slots, read only;
- `my_appointments()`: the patient's own appointments, read only;
- `book(slot, key)`, `move(appointment, slot, key)` and `cancel(appointment, key)`: one change each.

Every call is made as the signed-in patient, with their token, so the booking system itself refuses anything outside their own appointments. The agent has no other tools, and no way to write to the booking system except these.

## A run

1. The agent reads the request and the patient's appointments.
2. It searches for slots and proposes a change: the date, time, clinic and therapist.
3. The patient confirms or picks another. Only a confirmation lets the change through.
4. The agent makes the change and reports the booking system's answer, not its own.

A run has a limit of steps and of time. A request it can't finish within them, or one the tools can't do, such as a complaint, goes to staff with the chat and what the agent found.

## Errors

A change that times out may have happened. Each change carries an idempotency key, made once for that change, so sending it again books once. Before trying again, the agent reads the patient's appointments to see whether the change is there. A change that fails twice goes to staff.

## Tests

A test copy of the booking system, with patients and slots made for the tests, takes the agent's calls. Each test request runs several times, and passes only if every run leaves the bookings it should, as pass^k in Scoring an agent measures, since a patient gets one run, not the best of several. A run that books the wrong slot, or any slot without a confirmation, fails however polite its words.

## Cost

A request is {% $fig.steps %} calls of {% $fig.call_in %} tokens in and {% $fig.call_out %} out: {% $fig.request_in %} in and {% $fig.request_out %} out. A day of {% $fig.requests %} requests is {% $fig.day_in %} tokens in and {% $fig.day_out %} out: {% $fig.day_cost %} a day, {% $fig.per_request %} a request.

## The follow-up questions

- **A timeout:** the agent reads the patient's appointments. If the booking is there, it reports it; if not, it sends the same change with the same key, which can't book twice.
- **"All my appointments":** the agent lists the {% $fig.many %} appointments and asks the patient to confirm the list. It cancels each with its own key and reports each result, so one failure doesn't hide the others.
- **Testing:** the test copy and the test requests, each run several times, scored by the bookings left. The agent books for real patients only after it passes, and its first weeks are watched by staff.
