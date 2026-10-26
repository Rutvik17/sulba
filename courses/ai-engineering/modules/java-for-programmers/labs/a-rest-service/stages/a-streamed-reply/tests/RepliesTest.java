import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

class RepliesTest {
    static final JsonMapper JSON = JsonMapper.builder().build();
    static final HttpClient CLIENT =
            HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
    static final Duration SOON = Duration.ofSeconds(10);
    static final String ASK = "{\"content\":\"  Where's my replacement card?  \"}";

    /** One step of a scripted reply: a pause, then an event or a failure. */
    record Step(Duration pause, Agent.Event event, CountDownLatch after) {
        static Step of(Agent.Event event) {
            return new Step(Duration.ZERO, event, null);
        }
    }

    /** An agent whose replies follow a script, each on a thread of its own, which notes each
     * message it's given and each reply that's closed. */
    static final class Scripted implements Agent {
        final Function<String, List<Step>> scripts;
        final ConcurrentLinkedQueue<String> messages = new ConcurrentLinkedQueue<>();
        final AtomicInteger closed = new AtomicInteger();

        Scripted(List<Step> script) {
            this(message -> script);
        }

        Scripted(Function<String, List<Step>> scripts) {
            this.scripts = scripts;
        }

        @Override
        public Reply reply(String message) {
            messages.add(message);
            var script = scripts.apply(message);
            var events = new LinkedBlockingQueue<Object>();
            var writer = Thread.ofVirtual().start(() -> {
                try {
                    for (var step : script) {
                        if (step.after() != null) {
                            step.after().await();
                        }
                        Thread.sleep(step.pause());
                        events.put(step.event() == null ? new Failed("The model answered 500.") : step.event());
                    }
                } catch (InterruptedException stopped) {
                    // Closed: the reply stops.
                }
            });
            return new Reply() {
                @Override
                public Event next(Duration wait) throws Failed, TimeoutException, InterruptedException {
                    var next = events.poll(wait.toNanos(), TimeUnit.NANOSECONDS);
                    if (next == null) {
                        throw new TimeoutException();
                    }
                    if (next instanceof Failed failed) {
                        throw failed;
                    }
                    return (Event) next;
                }

                @Override
                public void close() {
                    writer.interrupt();
                    closed.incrementAndGet();
                }
            };
        }
    }

    record Sse(String event, JsonNode data) {}

    HttpServer server;

    HttpServer serve(Agent agent, Gate gate) throws IOException {
        server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        server.createContext("/messages", new Replies(agent, gate));
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        server.start();
        return server;
    }

    @AfterEach
    void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    HttpRequest.Builder request(String path, String type, String body) {
        var request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + server.getAddress().getPort() + path))
                .timeout(SOON)
                .POST(HttpRequest.BodyPublishers.ofString(body));
        if (type != null) {
            request.header("Content-Type", type);
        }
        return request;
    }

    HttpResponse<String> post(String path, String type, String body) throws IOException, InterruptedException {
        return CLIENT.send(request(path, type, body).build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> say(String body) throws IOException, InterruptedException {
        return post("/messages", "application/json", body);
    }

    /** The next event of a stream of server-sent events' lines, or null at its end. */
    static Sse next(Iterator<String> lines) {
        String event = null;
        var data = new StringBuilder();
        while (lines.hasNext()) {
            var line = lines.next();
            if (line.isEmpty()) {
                return new Sse(event, JSON.readTree(data.toString()));
            }
            if (line.startsWith("event: ")) {
                event = line.substring("event: ".length());
            } else if (line.startsWith("data: ")) {
                data.append(line.substring("data: ".length()));
            }
        }
        return null;
    }

    static List<Sse> events(String body) {
        var events = new ArrayList<Sse>();
        var lines = body.lines().iterator();
        for (var event = next(lines); event != null; event = next(lines)) {
            events.add(event);
        }
        return events;
    }

    static Sse sse(String event, String data) {
        return new Sse(event, JSON.readTree(data));
    }

    static void assertProblem(int status, String detail, HttpResponse<String> reply) {
        assertEquals(status, reply.statusCode(), reply.body());
        assertEquals("application/problem+json", reply.headers().firstValue("Content-Type").orElse(null));
        assertEquals(detail, JSON.readTree(reply.body()).path("detail").asString(null), reply.body());
    }

    @Test
    @DisplayName("tst_tgfm6z Sends the reply as server-sent events")
    void streams() throws Exception {
        var agent = new Scripted(List.of(
                Step.of(new Agent.Text("Your card")),
                Step.of(new Agent.Tool("list_tickets")),
                Step.of(new Agent.Text(" was mailed on Monday.")),
                Step.of(new Agent.Done("Your card was mailed on Monday."))));
        serve(agent, new Gate(2, 4, Duration.ofMinutes(1)));
        var reply = say(ASK);
        assertEquals(200, reply.statusCode());
        assertEquals("text/event-stream", reply.headers().firstValue("Content-Type").orElse(null));
        assertEquals(List.of(
                sse("text", "{\"delta\":\"Your card\"}"),
                sse("tool", "{\"name\":\"list_tickets\"}"),
                sse("text", "{\"delta\":\" was mailed on Monday.\"}"),
                sse("done", "{\"content\":\"Your card was mailed on Monday.\"}")), events(reply.body()));
        assertEquals(List.of("Where's my replacement card?"), List.copyOf(agent.messages));
        assertEquals(1, agent.closed.get());
    }

    @Test
    @DisplayName("tst_4yp0jb Sends each event as it comes")
    void flushes() throws Exception {
        var first = new CountDownLatch(1);
        var agent = new Scripted(List.of(
                Step.of(new Agent.Text("Your card")),
                new Step(Duration.ZERO, new Agent.Done("Your card was mailed."), first)));
        serve(agent, new Gate(2, 4, Duration.ofMinutes(1)));
        assertTimeoutPreemptively(SOON, () -> {
            var reply = CLIENT.send(request("/messages", "application/json", ASK).build(), HttpResponse.BodyHandlers.ofLines());
            var lines = reply.body().iterator();
            assertEquals(sse("text", "{\"delta\":\"Your card\"}"), next(lines));
            // The rest of the reply is written only once the first event has arrived.
            first.countDown();
            assertEquals(sse("done", "{\"content\":\"Your card was mailed.\"}"), next(lines));
        });
    }

    @Test
    @DisplayName("tst_q3bin7 Ends a reply that takes longer than the limit with an error event")
    void late() throws Exception {
        var steps = new ArrayList<Step>();
        for (var i = 0; i < 100; i++) {
            steps.add(new Step(Duration.ofMillis(200), new Agent.Text("Still writing. "), null));
        }
        var agent = new Scripted(steps);
        serve(agent, new Gate(2, 4, Duration.ofMillis(700)));
        var events = assertTimeoutPreemptively(SOON, () -> events(say(ASK).body()));
        var last = events.removeLast();
        assertEquals(sse("error", "{\"title\":\"The reply took too long.\"}"), last);
        assertTrue(events.size() >= 1 && events.size() <= 4, events.toString());
        assertTrue(events.stream().allMatch(event -> event.event().equals("text")), events.toString());
        assertEquals(1, agent.closed.get());
    }

    @Test
    @DisplayName("tst_7tc548 Ends a reply the model fails with an error event")
    void failed() throws Exception {
        var agent = new Scripted(List.of(Step.of(new Agent.Text("Your")), Step.of(null)));
        serve(agent, new Gate(2, 4, Duration.ofMinutes(1)));
        assertEquals(List.of(
                sse("text", "{\"delta\":\"Your\"}"),
                sse("error", "{\"title\":\"The desk couldn't reply.\"}")), events(say(ASK).body()));
        assertEquals(1, agent.closed.get());
    }

    @Test
    @DisplayName("tst_m3g6f3 Turns a caller away when the gate is full, saying when to try again")
    void busy() throws Exception {
        var held = new CountDownLatch(1);
        var agent = new Scripted(List.of(new Step(Duration.ZERO, new Agent.Done("Your card was mailed."), held)));
        serve(agent, new Gate(1, 0, Duration.ofSeconds(30)));
        assertTimeoutPreemptively(SOON, () -> {
            var first = CLIENT.sendAsync(request("/messages", "application/json", ASK).build(), HttpResponse.BodyHandlers.ofString());
            while (agent.messages.isEmpty()) {
                Thread.sleep(5);
            }
            var turnedAway = say(ASK);
            assertProblem(503, "The desk is answering as many callers as it can.", turnedAway);
            assertEquals("30", turnedAway.headers().firstValue("Retry-After").orElse(null));
            assertEquals(1, agent.messages.size());
            held.countDown();
            assertEquals(200, first.get().statusCode());
            assertEquals(200, say(ASK).statusCode());
        });
    }

    @Test
    @DisplayName("tst_mvsyq2 Gives the place back however the reply ends")
    void leaves() throws Exception {
        var writing = new ArrayList<Step>();
        for (var i = 0; i < 200; i++) {
            writing.add(new Step(Duration.ofMillis(50), new Agent.Text("Still writing. "), null));
        }
        var agent = new Scripted(message -> switch (message) {
            case "Fail." -> List.of(Step.of(new Agent.Text("Your")), Step.of(null));
            case "Hang up." -> writing;
            default -> List.of(Step.of(new Agent.Done("Your card was mailed.")));
        });
        serve(agent, new Gate(1, 0, Duration.ofSeconds(30)));
        assertTimeoutPreemptively(SOON, () -> {
            assertEquals("error", events(say("{\"content\":\"Fail.\"}").body()).getLast().event());
            // A caller who hangs up while the reply is written.
            try (var socket = new Socket(InetAddress.getLoopbackAddress(), server.getAddress().getPort())) {
                var body = "{\"content\":\"Hang up.\"}".getBytes(StandardCharsets.UTF_8);
                socket.getOutputStream().write(("POST /messages HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                        + "Content-Type: application/json\r\nContent-Length: " + body.length + "\r\n\r\n")
                        .getBytes(StandardCharsets.US_ASCII));
                socket.getOutputStream().write(body);
                InputStream in = socket.getInputStream();
                in.read();
            }
            var reply = say(ASK);
            while (reply.statusCode() == 503) {
                Thread.sleep(50);
                reply = say(ASK);
            }
            assertEquals("done", events(reply.body()).getLast().event());
        });
        assertEquals(3, agent.closed.get());
    }

    @Test
    @DisplayName("tst_mocprv Refuses a message that doesn't fit, without asking the agent")
    void unfit() throws Exception {
        var agent = new Scripted(List.of(Step.of(new Agent.Done("Hello."))));
        serve(agent, new Gate(2, 4, Duration.ofMinutes(1)));
        var detail = "A message is 1 to 2,000 characters, without the spaces at its ends.";
        assertProblem(422, detail, say("{\"content\":\"   \"}"));
        assertProblem(422, detail, say("{\"content\":\"" + "a".repeat(2001) + "\"}"));
        assertProblem(422, "The request's content doesn't fit.", say("{\"text\":\"Where's my card?\"}"));
        assertProblem(422, "The request's content doesn't fit.", say("{}"));
        assertProblem(400, "The request's body isn't JSON.", say("Where's my card?"));
        assertProblem(415, "The desk reads a request's body as application/json.",
                post("/messages", "text/plain", "Where's my card?"));
        assertTrue(agent.messages.isEmpty());
        assertEquals(200, say("{\"content\":\" " + "a".repeat(2000) + " \"}").statusCode());
    }

    @Test
    @DisplayName("tst_j5lzxv Answers only a POST to /messages")
    void address() throws Exception {
        serve(new Scripted(List.of(Step.of(new Agent.Done("Hello.")))), new Gate(2, 4, Duration.ofMinutes(1)));
        var reply = CLIENT.send(request("/messages", null, "").GET().build(), HttpResponse.BodyHandlers.ofString());
        assertProblem(405, null, reply);
        assertEquals("POST", reply.headers().firstValue("Allow").orElse(null));
        assertProblem(404, null, post("/messages/1", "application/json", ASK));
        assertProblem(404, null, post("/messagesX", "application/json", ASK));
    }
}
