package tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import gateway.Bucket;
import gateway.Server;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Instant;
import java.time.InstantSource;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

class GatewayTest {
    /** A clock that moves only when a test moves it. */
    static final class Fake implements InstantSource {
        final AtomicLong millis = new AtomicLong();

        @Override
        public Instant instant() {
            return Instant.ofEpochMilli(millis.get());
        }
    }

    @Test
    @DisplayName("tst_aaaaaa Lets a burst through, then refills with time")
    void bucket() {
        Fake clock = new Fake();
        Bucket bucket = new Bucket(clock, 2, 2);
        assertTrue(bucket.allow());
        assertTrue(bucket.allow());
        assertFalse(bucket.allow());
        clock.millis.addAndGet(3_600_000);
        assertTrue(bucket.allow());
    }

    @Test
    @DisplayName("tst_bbbbbb Answers JSON over HTTP, in UTF-8")
    void server() throws Exception {
        var server = Server.start();
        try (var client = HttpClient.newHttpClient()) {
            var response = client.send(
                    HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/healthz")).build(),
                    HttpResponse.BodyHandlers.ofString());
            var body = JsonMapper.builder().build().readTree(response.body());
            assertEquals(200, response.statusCode());
            assertEquals("é", body.get("naïve").asString());
        } finally {
            server.stop(0);
        }
    }

    @Test
    @DisplayName("tst_cccccc Fails with its message")
    void fails() {
        assertEquals(3, 1 + 1, "one and one");
    }

    @Test
    @DisplayName("tst_dddddd Throws from the learner's code")
    void throwsFromCode() {
        assertEquals(1, Server.first(new int[0]));
    }

    @Test
    @DisplayName("tst_eeeeee Runs ten thousand virtual threads")
    void threads() throws Exception {
        var count = new AtomicLong();
        try (var executor = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                executor.submit(() -> {
                    Thread.sleep(10);
                    return count.incrementAndGet();
                });
            }
        }
        assertEquals(10_000, count.get());
    }
}
