import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
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

class AppChecksTest {
    static final List<String> NAMES =
            List.of("DESK_HOST", "DESK_PORT", "DESK_RUNNING", "DESK_WAITING", "DESK_SECONDS", "DESK_GRACE");
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

    /** That the settings are refused, naming each wrong variable and no other. */
    static void assertWrong(Map<String, String> environment, String... wrong) {
        var message = assertThrows(IllegalArgumentException.class, () -> App.settings(environment)).getMessage();
        for (var name : NAMES) {
            assertEquals(List.of(wrong).contains(name), message.contains(name), name + " in: " + message);
        }
    }

    @Test
    @DisplayName("tst_oxfedr Settings that fit")
    void settings() {
        assertWrong(Map.of("DESK_PORT", "eighty", "DESK_RUNNING", "0"), "DESK_PORT", "DESK_RUNNING");
        assertWrong(Map.of("DESK_PORT", "65536"), "DESK_PORT");
        assertWrong(Map.of("DESK_PORT", "-1"), "DESK_PORT");
        assertWrong(Map.of("DESK_PORT", ""), "DESK_PORT");
        assertWrong(Map.of("DESK_WAITING", "-1", "DESK_GRACE", "-3"), "DESK_WAITING", "DESK_GRACE");
        assertWrong(Map.of("DESK_SECONDS", "0"), "DESK_SECONDS");
        assertWrong(Map.of("DESK_SECONDS", "1.5"), "DESK_SECONDS");
        assertWrong(Map.of("DESK_HOST", " "), "DESK_HOST");
        assertWrong(Map.of("DESK_HOST", "", "DESK_PORT", "x", "DESK_RUNNING", "-2", "DESK_WAITING", "many",
                "DESK_SECONDS", "", "DESK_GRACE", "soon"), NAMES.toArray(String[]::new));
        assertEquals(new App.Settings("127.0.0.1", 0, 1, 0, Duration.ofSeconds(1), 0), App.settings(Map.of(
                "DESK_PORT", "0", "DESK_RUNNING", "1", "DESK_WAITING", "0", "DESK_SECONDS", "1", "DESK_GRACE", "0")));
    }

    @Test
    @DisplayName("tst_y8y96l The gate from the settings")
    void gate() throws Exception {
        var agent = new Slow(Duration.ofSeconds(3));
        var app = start(agent, Map.of("DESK_RUNNING", "1", "DESK_WAITING", "0", "DESK_SECONDS", "7", "DESK_GRACE", "0"));
        try {
            CLIENT.sendAsync(message(app), HttpResponse.BodyHandlers.discarding());
            awaitStarted(agent, 1);
            var turnedAway = CLIENT.send(message(app), HttpResponse.BodyHandlers.ofString());
            assertEquals(503, turnedAway.statusCode());
            assertEquals("7", turnedAway.headers().firstValue("Retry-After").orElse(null));
        } finally {
            app.stop();
        }
        agent = new Slow(Duration.ofSeconds(3));
        app = start(agent, Map.of("DESK_RUNNING", "2", "DESK_WAITING", "0", "DESK_GRACE", "0"));
        try {
            CLIENT.sendAsync(message(app), HttpResponse.BodyHandlers.discarding());
            CLIENT.sendAsync(message(app), HttpResponse.BodyHandlers.discarding());
            awaitStarted(agent, 2);
            assertEquals(503, CLIENT.send(message(app), HttpResponse.BodyHandlers.ofString()).statusCode());
        } finally {
            app.stop();
        }
    }

    @Test
    @DisplayName("tst_r1o3cw A reply in flight gets to finish")
    void finishes() throws Exception {
        var agent = new Slow(Duration.ofMillis(1500));
        var app = start(agent, Map.of("DESK_GRACE", "5"));
        var reply = CLIENT.sendAsync(message(app), HttpResponse.BodyHandlers.ofString());
        awaitStarted(agent, 1);
        assertTimeoutPreemptively(Duration.ofSeconds(10), app::stop);
        assertTrue(reply.get().body().contains("event: done"), reply.get().body());
    }

    @Test
    @DisplayName("tst_nhwh7s The grace has an end")
    void grace() throws Exception {
        var agent = new Slow(Duration.ofMinutes(1));
        var app = start(agent, Map.of("DESK_GRACE", "1"));
        var reply = CLIENT.sendAsync(message(app), HttpResponse.BodyHandlers.ofString());
        awaitStarted(agent, 1);
        assertTimeoutPreemptively(Duration.ofSeconds(6), app::stop);
        assertEquals(1, agent.closed.get(), "The reply still runs.");
        var body = assertThrows(Exception.class, reply::get);
        assertFalse(body.toString().contains("event: done"));
    }
}
