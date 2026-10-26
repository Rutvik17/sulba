The desk keeps one caller's tickets and booked callbacks, and the times each service's advisers are free. In `Desk.java`, write `Desk`, made from the caller's tickets and the free times, as a map from each service to its days, and from each day to that day's times:

```java
new Desk(List<Ticket> tickets, Map<Service, Map<LocalDate, List<LocalTime>>> free)
```

The desk keeps its own copies, so changing what it was given changes nothing in the desk, and what it gives out can't change it: each list it gives throws `UnsupportedOperationException` if a caller tries to change it.

- `tickets()` gives the caller's tickets, in the order the desk was given them and then opened them, and `callbacks()` the callbacks booked, as `Callback(ticket, day, time)` records, in the order they were booked.
- `free(service, day)` gives the times the service's advisers are free that day, in order, and none for a day the desk has no times for.
- `listTickets(status)` gives the tickets with the status, by their lines, as the Python desk did, and how many have the other status: `The caller's open tickets:`, a line for each, then `They have 1 closed ticket: list_tickets with status "closed" lists them.`, with `tickets` for more than one. With none, it's `The caller has no open tickets.`
- `openTicket(service, summary)` opens a ticket and gives it. The first it opens is `T-3001`, the next `T-3002`. A summary the ticket refuses opens nothing, and uses up no number.

A booking the desk can't make is refused with `Desk.Refused`, a checked exception whose message says why, for the model to read:

- `bookCallback(ticket, day, time)` books an adviser of the ticket's service, and gives the callback. With no open ticket by that id, it's refused with `The caller has no open ticket T-9.` At a time the advisers aren't free, it's `The advisers aren't free on Monday 2026-11-02 at 11:00. They're free at 09:00, 10:00, 14:00.`, or `They're free at no time that day.` A booked time is no longer free.
- `cancelCallback(ticket, day, time)` cancels a callback and frees its time again. A callback that isn't booked is refused with `The caller has no callback about T-2041 on 2026-11-02 at 09:00.`

In JSON, a callback's time is in hours and minutes: `{"ticket":"T-2041","day":"2026-11-02","time":"09:00"}`.

```java
public List<Ticket> tickets()
public List<Callback> callbacks()
public List<LocalTime> free(Service service, LocalDate day)
public String listTickets(Ticket.Status status)
public Ticket openTicket(Service service, String summary)
public Callback bookCallback(String ticket, LocalDate day, LocalTime time) throws Refused
public void cancelCallback(String ticket, LocalDate day, LocalTime time) throws Refused
```
