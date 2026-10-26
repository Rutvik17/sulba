import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
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

class ServerChecksTest {
    static final JsonMapper JSON = JsonMapper.builder().build();
    static final HttpClient CLIENT =
            HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
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

    HttpRequest.Builder request(String path) {
        return HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.getAddress().getPort() + path))
                .timeout(Duration.ofSeconds(3));
    }

    HttpResponse<String> send(HttpRequest.Builder request) throws IOException, InterruptedException {
        return CLIENT.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> post(String path, String body) throws IOException, InterruptedException {
        return send(request(path).header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(body)));
    }

    @Test
    @DisplayName("tst_egd3dw A slow caller holds up no one")
    void slow() throws Exception {
        try (var caller = new Socket(InetAddress.getLoopbackAddress(), server.getAddress().getPort())) {
            // A ticket whose body has 100 bytes, of which the caller has sent 10 so far.
            caller.getOutputStream().write(("POST /tickets HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n"
                    + "Content-Length: 100\r\n\r\n{\"service\"").getBytes(StandardCharsets.US_ASCII));
            caller.getOutputStream().flush();
            Thread.sleep(1000);
            assertEquals(200, send(request("/health")).statusCode());
            assertEquals(200, send(request("/tickets")).statusCode());
        }
    }

    @Test
    @DisplayName("tst_y39bs3 A request's body reaches the desk")
    void bodies() throws Exception {
        var opened = post("/tickets", "{\"service\":\"va\",\"summary\":\"My GI Bill payment is late.\"}");
        assertEquals(201, opened.statusCode(), opened.body());
        var reply = post("/messages", "{\"content\":\"Where's my card?\"}");
        assertEquals(200, reply.statusCode(), reply.body());
        assertTrue(reply.body().contains("event: done"), reply.body());
        assertTrue(log.stream().anyMatch(line -> line.startsWith("POST /tickets 201 ")), log.toString());
        assertTrue(log.stream().anyMatch(line -> line.startsWith("POST /messages 200 ")), log.toString());
    }

    @Test
    @DisplayName("tst_ffrwoe A health check of the wrong kind gets its answer")
    void health() throws Exception {
        var reply = send(request("/health").POST(HttpRequest.BodyPublishers.noBody()));
        assertEquals(405, reply.statusCode());
        assertEquals("GET", reply.headers().firstValue("Allow").orElse(null));
        assertEquals("application/problem+json", reply.headers().firstValue("Content-Type").orElse(null));
        assertEquals(404, send(request("/healthz")).statusCode());
    }

    @Test
    @DisplayName("tst_nzqd0s Every address answers with problem details")
    void everywhere() throws Exception {
        for (var path : List.of("/", "/callbacks", "/tickets/T-2041/notes")) {
            var reply = send(request(path));
            assertEquals(404, reply.statusCode(), path);
            assertEquals("application/problem+json", reply.headers().firstValue("Content-Type").orElse(null), path);
            assertEquals(JSON.readTree("{\"type\":\"about:blank\",\"title\":\"Not Found\",\"status\":404}"), JSON.readTree(reply.body()));
        }
        assertEquals(200, send(request("/tickets")).statusCode());
    }
}
