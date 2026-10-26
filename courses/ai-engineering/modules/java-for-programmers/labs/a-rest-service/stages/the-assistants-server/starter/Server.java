import com.sun.net.httpserver.Filter;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.function.Consumer;

/** The desk's server: the API, the replies and a health check on one HttpServer, with a line in
 * the log for each request. */
public final class Server {
    private Server() {}

    /** Starts the desk's server at the address, and gives it. */
    public static HttpServer start(InetSocketAddress address, Desk desk, Agent agent, Gate gate, Consumer<String> log)
            throws IOException {
        var server = HttpServer.create(address, 0);
        var logged = new Logged(log);
        server.createContext("/tickets", new Api(desk)).getFilters().add(logged);
        server.createContext("/messages", new Replies(agent, gate)).getFilters().add(logged);
        server.createContext("/health", Server::health).getFilters().add(logged);
        server.start();
        return server;
    }

    private static void health(HttpExchange exchange) throws IOException {
        if (!exchange.getRequestURI().getPath().equals("/health")) {
            problem(exchange, Problems.of(404, null));
            return;
        }
        if (!exchange.getRequestMethod().equals("GET")) {
            exchange.getResponseHeaders().set("Allow", "GET");
            problem(exchange, Problems.of(405, null));
            return;
        }
        var body = "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(200, body.length);
        try (var out = exchange.getResponseBody()) {
            out.write(body);
        }
    }

    private static void problem(HttpExchange exchange, Problems.Problem problem) throws IOException {
        var body = Problems.json(problem).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", Problems.MEDIA_TYPE);
        exchange.sendResponseHeaders(problem.status(), body.length);
        exchange.getResponseBody().write(body);
    }

    /** Writes a line to the log for each request: its method, its path, the status it got, the
     * bytes it sent and the milliseconds it took. */
    private static final class Logged extends Filter {
        private final Consumer<String> log;

        Logged(Consumer<String> log) {
            this.log = log;
        }

        @Override
        public void doFilter(HttpExchange exchange, Chain chain) throws IOException {
            var start = System.nanoTime();
            var size = exchange.getRequestBody().readAllBytes().length;
            chain.doFilter(exchange);
            log.accept(exchange.getRequestMethod() + " " + exchange.getRequestURI().getPath() + " "
                    + exchange.getResponseCode() + " " + size + " " + (System.nanoTime() - start) / 1_000_000 + "ms");
        }

        @Override
        public String description() {
            return "A line in the log for each request";
        }
    }
}
