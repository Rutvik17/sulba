import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedQueue;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

class ServerTest {
    static final JsonMapper JSON = JsonMapper.builder().build();
    static final HttpClient CLIENT =
            HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();

    /** An agent that answers every message at once. */
    static final Agent AGENT = message -> new Agent.Reply() {
        @Override
        public Agent.Event next(Duration wait) {
            return new Agent.Done("Your card was mailed on Monday.");
        }

        @Override
        public void close() {}
    };

    final ConcurrentLinkedQueue<String> log = new ConcurrentLinkedQueue<>();
    HttpServer server;

    @BeforeEach
    void start() throws IOException {
        var desk = new Desk(
                List.of(new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, "My replacement Social Security card hasn't come.")),
                Map.of(Service.SSA, Map.of(LocalDate.of(2026, 11, 2), List.of(LocalTime.of(9, 0)))));
        server = Server.start(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), desk, AGENT,
                new Gate(2, 4, Duration.ofMinutes(1)), log::add);
    }

    @AfterEach
    void stop() {
        server.stop(0);
    }

    HttpResponse<String> get(String path) throws IOException, InterruptedException {
        return CLIENT.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.getAddress().getPort() + path))
                .timeout(Duration.ofSeconds(10)).build(), HttpResponse.BodyHandlers.ofString());
    }

    /** The log's lines once it has `count` of them, or after five seconds. A request's line is
     * written once its reply has gone, so it can come a moment after the caller has the reply. */
    List<String> lines(int count) throws InterruptedException {
        var deadline = System.nanoTime() + Duration.ofSeconds(5).toNanos();
        while (log.size() < count && System.nanoTime() < deadline) {
            Thread.sleep(10);
        }
        return List.copyOf(log);
    }

    @Test
    @DisplayName("tst_gcsvi9 Answers its health check")
    void health() throws Exception {
        var reply = get("/health");
        assertEquals(200, reply.statusCode());
        assertEquals("application/json", reply.headers().firstValue("Content-Type").orElse(null));
        assertEquals(JSON.readTree("{\"status\":\"ok\"}"), JSON.readTree(reply.body()));
    }

    @Test
    @DisplayName("tst_w1w48j Serves the desk's tickets")
    void tickets() throws Exception {
        assertEquals("T-2041", JSON.readTree(get("/tickets").body()).get(0).get("ticket").asString());
        assertEquals(200, get("/tickets/T-2041").statusCode());
    }

    @Test
    @DisplayName("tst_ixpvr2 Answers a ticket that isn't there with a 404")
    void missing() throws Exception {
        var reply = get("/tickets/T-9");
        assertEquals(404, reply.statusCode());
        assertEquals("application/problem+json", reply.headers().firstValue("Content-Type").orElse(null));
    }

    @Test
    @DisplayName("tst_17exj0 Writes a line to the log for each request")
    void logs() throws Exception {
        get("/tickets");
        get("/health");
        var lines = lines(2);
        assertEquals(2, lines.size(), lines.toString());
        assertTrue(lines.stream().anyMatch(line -> line.startsWith("GET /tickets 200 ")), lines.toString());
        assertTrue(lines.stream().anyMatch(line -> line.startsWith("GET /health 200 ")), lines.toString());
    }
}
