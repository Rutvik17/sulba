import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.TimeoutException;

/** The desk's replies: the caller's message in, and the agent's reply out as server-sent events,
 * each piece as it comes, through the gate in front of the model. */
public final class Replies implements HttpHandler {
    /** The caller's message. */
    public record Say(String content) {}

    private final Agent agent;
    private final Gate gate;

    public Replies(Agent agent, Gate gate) {
        this.agent = agent;
        this.gate = gate;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        try (exchange) {
            try {
                reply(exchange);
            } catch (RuntimeException error) {
                problem(exchange, Problems.of(error));
            }
        }
    }

    private void reply(HttpExchange exchange) throws IOException {
        if (!exchange.getRequestURI().getPath().equals("/messages")) {
            problem(exchange, Problems.of(404, null));
            return;
        }
        if (!exchange.getRequestMethod().equals("POST")) {
            exchange.getResponseHeaders().set("Allow", "POST");
            problem(exchange, Problems.of(405, null));
            return;
        }
        var type = exchange.getRequestHeaders().getFirst("Content-Type");
        if (type == null || !type.split(";", 2)[0].strip().equalsIgnoreCase("application/json")) {
            problem(exchange, Problems.of(415, "The desk reads a request's body as application/json."));
            return;
        }
        var content = Api.JSON.readValue(exchange.getRequestBody(), Say.class).content().strip();
        if (content.isEmpty() || content.length() > 2000) {
            problem(exchange, Problems.of(422, "A message is 1 to 2,000 characters, without the spaces at its ends."));
            return;
        }
        try {
            gate.enter();
        } catch (Gate.Busy busy) {
            exchange.getResponseHeaders().set("Retry-After", Long.toString(busy.retryAfter()));
            problem(exchange, Problems.of(503, "The desk is answering as many callers as it can."));
            return;
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return;
        }
        try {
            stream(exchange, content);
        } finally {
            gate.leave();
        }
    }

    private void stream(HttpExchange exchange, String content) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "text/event-stream");
        exchange.sendResponseHeaders(200, 0);
        var out = exchange.getResponseBody();
        var deadline = System.nanoTime() + gate.limit().toNanos();
        try (var reply = agent.reply(content)) {
            while (true) {
                var event = reply.next(Duration.ofNanos(Math.max(deadline - System.nanoTime(), 0)));
                switch (event) {
                    case Agent.Text text -> send(out, "text", Map.of("delta", text.delta()));
                    case Agent.Tool tool -> send(out, "tool", Map.of("name", tool.name()));
                    case Agent.Done done -> {
                        send(out, "done", Map.of("content", done.content()));
                        return;
                    }
                }
            }
        } catch (TimeoutException late) {
            send(out, "error", Map.of("title", "The reply took too long."));
        } catch (Agent.Failed failed) {
            send(out, "error", Map.of("title", "The desk couldn't reply."));
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    /** Sends one event, at once. */
    private static void send(OutputStream out, String event, Map<String, String> data) throws IOException {
        out.write(("event: " + event + "\ndata: " + Api.JSON.writeValueAsString(data) + "\n\n")
                .getBytes(StandardCharsets.UTF_8));
        out.flush();
    }

    private static void problem(HttpExchange exchange, Problems.Problem problem) throws IOException {
        var body = Problems.json(problem).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", Problems.MEDIA_TYPE);
        exchange.sendResponseHeaders(problem.status(), body.length);
        exchange.getResponseBody().write(body);
    }
}
