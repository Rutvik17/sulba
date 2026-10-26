import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class AppTest {
    static final HttpClient CLIENT =
            HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();

    /** An agent whose every reply gives a piece of text at once and the whole reply after a
     * pause, and that counts the replies it starts and the replies closed. */
    static final class Slow implements Agent {
        final Duration pause;
        final AtomicInteger started = new AtomicInteger();
        final AtomicInteger closed = new AtomicInteger();

        Slow(Duration pause) {
            this.pause = pause;
        }

        @Override
        public Reply reply(String message) {
            started.incrementAndGet();
            var start = System.nanoTime();
            return new Reply() {
                boolean texted;

                @Override
                public Event next(Duration wait) throws TimeoutException, InterruptedException {
                    if (!texted) {
                        texted = true;
                        return new Text("Your card");
                    }
                    var left = Duration.ofNanos(pause.toNanos() - (System.nanoTime() - start));
                    if (left.compareTo(wait) > 0) {
                        Thread.sleep(wait);
                        throw new TimeoutException();
                    }
                    Thread.sleep(left.isNegative() ? Duration.ZERO : left);
                    return new Done("Your card was mailed on Monday.");
                }

                @Override
                public void close() {
                    closed.incrementAndGet();
                }
            };
        }
    }

    static Desk desk() {
        return new Desk(
                List.of(new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, "My replacement Social Security card hasn't come.")),
                Map.of(Service.SSA, Map.of(LocalDate.of(2026, 11, 2), List.of(LocalTime.of(9, 0)))));
    }

    static App start(Agent agent, Map<String, String> environment) throws IOException {
        var variables = new HashMap<>(Map.of("DESK_PORT", "0"));
        variables.putAll(environment);
        return App.start(App.settings(variables), desk(), agent, line -> {});
    }

    static HttpRequest.Builder request(App app, String path) {
        return HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + app.address().getPort() + path))
                .timeout(Duration.ofSeconds(20));
    }

    static HttpRequest message(App app) {
        return request(app, "/messages").header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{\"content\":\"Where's my card?\"}")).build();
    }

    static void awaitStarted(Slow agent, int replies) throws InterruptedException {
        while (agent.started.get() < replies) {
            Thread.sleep(5);
        }
    }

    @Test
    @DisplayName("tst_us2ucv Takes each setting's default when its variable isn't set")
    void defaults() {
        assertEquals(new App.Settings("127.0.0.1", 8080, 2, 8, Duration.ofSeconds(120), 10), App.settings(Map.of()));
        assertEquals(new App.Settings("0.0.0.0", 9090, 4, 8, Duration.ofSeconds(120), 10), App.settings(Map.of(
                "DESK_HOST", "0.0.0.0", "DESK_PORT", "9090", "DESK_RUNNING", "4", "PATH", "/usr/bin")));
    }

    @Test
    @DisplayName("tst_7rmi1m Serves the desk at its address until it stops")
    void serves() throws Exception {
        var app = start(new Slow(Duration.ZERO), Map.of("DESK_GRACE", "0"));
        assertNotEquals(0, app.address().getPort());
        assertEquals(200, CLIENT.send(request(app, "/tickets").build(), HttpResponse.BodyHandlers.ofString()).statusCode());
        assertEquals(200, CLIENT.send(request(app, "/health").build(), HttpResponse.BodyHandlers.ofString()).statusCode());
        app.stop();
        assertThrows(IOException.class, () -> CLIENT.send(request(app, "/health").build(), HttpResponse.BodyHandlers.ofString()));
    }

    @Test
    @DisplayName("tst_1mj0u1 Replies to a message")
    void replies() throws Exception {
        var app = start(new Slow(Duration.ZERO), Map.of("DESK_GRACE", "0"));
        var reply = CLIENT.send(message(app), HttpResponse.BodyHandlers.ofString());
        assertEquals(200, reply.statusCode());
        assertTrue(reply.body().contains("event: done"), reply.body());
        app.stop();
    }
}
