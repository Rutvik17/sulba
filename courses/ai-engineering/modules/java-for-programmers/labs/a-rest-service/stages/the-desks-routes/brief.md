The desk's API from Shipping full stack ran on FastAPI. This lab builds it again on the JDK's own HTTP server, `com.sun.net.httpserver`, from the desk you built in Records, interfaces and exceptions, which the lab gives you: `Service.java`, `Ticket.java`, `Desk.java` and `Problems.java`.

In `Api.java`, write `Api`, an `HttpHandler` on one `Desk`, which a server gives every request to:

```java
var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 8080), 0);
server.createContext("/", new Api(desk));
```

Its routes, each answering in JSON as `application/json`:

- `GET /tickets` gives the caller's tickets, as `Ticket` writes them: `[{"ticket":"T-2041","service":"ssa","status":"open","summary":"..."}, ...]`.
- `POST /tickets` takes a `NewTicket`, `{"service":"va","summary":"My GI Bill payment is late."}`, and opens a ticket on the desk. It answers 201 with the ticket, and the ticket's address, `/tickets/T-3001`, in `Location`.
- `GET /tickets/{id}` gives the ticket with the id, or a 404 with the detail `There's no ticket with this id.`
- `POST /tickets/{id}/callbacks` takes a `NewCallback`, `{"day":"2026-11-02","time":"09:00"}`, with the time in hours and minutes, books it on the ticket, and answers 201 with the callback. A ticket that isn't there gets the same 404 as above, and a booking the desk refuses gets a 409 with the desk's message.

Every error is a problem details object, from `Problems`, as `application/problem+json`:

- an address the API doesn't have, such as `/ticketsX` or `/tickets/`, gets a 404;
- a method an address doesn't take gets a 405, with the methods it does take in `Allow`, such as `GET, POST`;
- a `POST` whose `Content-Type` isn't `application/json`, in any case and with any parameters, gets a 415 with the detail `The desk reads a request's body as application/json.`;
- a body that isn't JSON, or that doesn't fit its record, gets the problem `Problems.of` gives for Jackson's error. A field the record doesn't have doesn't fit, and neither does one that's missing or null.
- a summary the ticket refuses gets a 422 with the ticket's message, and opens nothing.

Many callers' requests arrive at once, each on a thread of its own, and the desk isn't safe for two threads at once: let only one thread use it at a time.

```java
public record NewTicket(Service service, String summary)
public record NewCallback(LocalDate day, LocalTime time)
public Api(Desk desk)
public void handle(HttpExchange exchange) throws IOException
```

The tests start a server on a free port, with a thread for each request, and send their requests with the JDK's `HttpClient`.
