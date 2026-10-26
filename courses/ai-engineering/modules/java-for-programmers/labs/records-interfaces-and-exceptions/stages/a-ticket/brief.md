The benefits office runs its services in Java, and its IT team wants the help desk's code in Java too, behaving as the Python desk does. This lab rebuilds the desk's model: its tickets, its callbacks, the tools a model calls, and its errors. The lab gives you `Service.java`, the four services, each with the id JSON gives it, such as `ssa`, and its name in a sentence, such as `Social Security`.

A ticket comes first. In `Ticket.java`, write the record `Ticket(id, service, status, summary)`, whose `Status` is `OPEN` or `CLOSED`. A ticket checks itself as it's made:

- A part that's `null` gives a `NullPointerException` whose message is the part's name, such as `service`.
- The id is `T-` and a number, such as `T-2041`. Any other gives an `IllegalArgumentException` with the message `A ticket's id is T- and its number, like T-2041, not "2041".`, quoting the id it got.
- The summary is kept without the space around it. A summary that's blank gives `A ticket's summary is a sentence about the case.`, and one over 300 characters gives `A ticket's summary is at most 300 characters, not 301.`, with its length.

Then three methods:

- `isOpen()` says whether the ticket is open.
- `closed()` gives the ticket closed, and leaves the ticket it's called on as it was.
- `line()` gives the ticket as the desk lists it: `T-2041: Social Security, My replacement Social Security card hasn't come.`

In JSON, a ticket has four fields: `ticket`, its id; `service`, the service's id; `status`, `open` or `closed`; and `summary`. The desk reads tickets from JSON and writes them to it with Jackson, so a ticket read from JSON is checked as one made in Java is.

```java
public record Ticket(String id, Service service, Status status, String summary)
public boolean isOpen()
public Ticket closed()
public String line()
```

The tests read and write JSON with `JsonMapper.builder().build()`.
