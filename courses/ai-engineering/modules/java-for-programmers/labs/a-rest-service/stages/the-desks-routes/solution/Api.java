import com.fasterxml.jackson.annotation.JsonFormat;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.json.JsonMapper;

/** The desk's API: the caller's tickets and the callbacks booked on them, as JSON, with every
 * error as problem details. */
public final class Api implements HttpHandler {
    /** What opening a ticket takes. */
    public record NewTicket(Service service, String summary) {}

    /** What booking a callback takes. */
    public record NewCallback(LocalDate day, @JsonFormat(pattern = "HH:mm") LocalTime time) {}

    /** How the API reads and writes JSON: a field a record doesn't have, or a field that's
     * missing or null, doesn't fit. */
    public static final JsonMapper JSON = JsonMapper.builder()
            .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .enable(DeserializationFeature.FAIL_ON_NULL_CREATOR_PROPERTIES)
            .build();

    private static final Pattern TICKET = Pattern.compile("/tickets/([^/]+)");
    private static final Pattern CALLBACKS = Pattern.compile("/tickets/([^/]+)/callbacks");

    private final Desk desk;

    public Api(Desk desk) {
        this.desk = desk;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        try (exchange) {
            try {
                route(exchange);
            } catch (Desk.Refused | RuntimeException error) {
                problem(exchange, Problems.of(error));
            }
        }
    }

    private void route(HttpExchange exchange) throws IOException, Desk.Refused {
        var path = exchange.getRequestURI().getPath();
        var method = exchange.getRequestMethod();
        var ticket = TICKET.matcher(path);
        var callbacks = CALLBACKS.matcher(path);
        if (path.equals("/tickets")) {
            switch (method) {
                case "GET" -> json(exchange, 200, tickets());
                case "POST" -> open(exchange);
                default -> notAllowed(exchange, "GET, POST");
            }
        } else if (ticket.matches()) {
            if (!method.equals("GET")) {
                notAllowed(exchange, "GET");
                return;
            }
            var found = find(ticket.group(1));
            if (found.isPresent()) {
                json(exchange, 200, found.get());
            } else {
                problem(exchange, Problems.of(404, "There's no ticket with this id."));
            }
        } else if (callbacks.matches()) {
            if (!method.equals("POST")) {
                notAllowed(exchange, "POST");
                return;
            }
            book(exchange, callbacks.group(1));
        } else {
            problem(exchange, Problems.of(404, null));
        }
    }

    private void open(HttpExchange exchange) throws IOException {
        if (!isJson(exchange)) {
            problem(exchange, unsupported());
            return;
        }
        var request = JSON.readValue(exchange.getRequestBody(), NewTicket.class);
        Ticket ticket;
        try {
            synchronized (desk) {
                ticket = desk.openTicket(request.service(), request.summary());
            }
        } catch (IllegalArgumentException refused) {
            problem(exchange, Problems.of(422, refused.getMessage()));
            return;
        }
        exchange.getResponseHeaders().set("Location", "/tickets/" + ticket.id());
        json(exchange, 201, ticket);
    }

    private void book(HttpExchange exchange, String id) throws IOException, Desk.Refused {
        if (!isJson(exchange)) {
            problem(exchange, unsupported());
            return;
        }
        if (find(id).isEmpty()) {
            problem(exchange, Problems.of(404, "There's no ticket with this id."));
            return;
        }
        var request = JSON.readValue(exchange.getRequestBody(), NewCallback.class);
        Desk.Callback callback;
        synchronized (desk) {
            callback = desk.bookCallback(id, request.day(), request.time());
        }
        json(exchange, 201, callback);
    }

    private List<Ticket> tickets() {
        synchronized (desk) {
            return desk.tickets();
        }
    }

    private Optional<Ticket> find(String id) {
        return tickets().stream().filter(ticket -> ticket.id().equals(id)).findFirst();
    }

    private static boolean isJson(HttpExchange exchange) {
        var type = exchange.getRequestHeaders().getFirst("Content-Type");
        return type != null && type.split(";", 2)[0].strip().equalsIgnoreCase("application/json");
    }

    private static Problems.Problem unsupported() {
        return Problems.of(415, "The desk reads a request's body as application/json.");
    }

    private static void notAllowed(HttpExchange exchange, String methods) throws IOException {
        exchange.getResponseHeaders().set("Allow", methods);
        problem(exchange, Problems.of(405, null));
    }

    private static void json(HttpExchange exchange, int status, Object value) throws IOException {
        send(exchange, status, "application/json", JSON.writeValueAsBytes(value));
    }

    private static void problem(HttpExchange exchange, Problems.Problem problem) throws IOException {
        send(exchange, problem.status(), Problems.MEDIA_TYPE, Problems.json(problem).getBytes(StandardCharsets.UTF_8));
    }

    private static void send(HttpExchange exchange, int status, String type, byte[] body) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", type);
        exchange.sendResponseHeaders(status, body.length);
        exchange.getResponseBody().write(body);
    }
}
