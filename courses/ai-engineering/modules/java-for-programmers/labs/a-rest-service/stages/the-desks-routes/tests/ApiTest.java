import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

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
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.json.JsonMapper;

class ApiTest {
    static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);
    static final Ticket CARD = new Ticket(
            "T-2041", Service.SSA, Ticket.Status.OPEN, "My replacement Social Security card hasn't come.");
    static final Ticket ADDRESS =
            new Ticket("T-1873", Service.DMV, Ticket.Status.CLOSED, "My new address isn't on my license.");
    static final String CARD_JSON = """
            {"ticket":"T-2041","service":"ssa","status":"open",
             "summary":"My replacement Social Security card hasn't come."}""";
    static final String ADDRESS_JSON = """
            {"ticket":"T-1873","service":"dmv","status":"closed",
             "summary":"My new address isn't on my license."}""";
    static final JsonMapper JSON = JsonMapper.builder().build();
    static final HttpClient CLIENT =
            HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();

    Desk desk;
    HttpServer server;

    /** Social Security's advisers are free on Monday at 9:00, 10:00 and 14:00. */
    @BeforeEach
    void serve() throws IOException {
        var free = new EnumMap<Service, Map<LocalDate, List<LocalTime>>>(Service.class);
        free.put(Service.SSA, Map.of(MONDAY, List.of(LocalTime.of(9, 0), LocalTime.of(10, 0), LocalTime.of(14, 0))));
        desk = new Desk(List.of(CARD, ADDRESS), free);
        server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        server.createContext("/", new Api(desk));
        server.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
        server.start();
    }

    @AfterEach
    void stop() {
        server.stop(0);
    }

    HttpResponse<String> send(String method, String path, String type, String body)
            throws IOException, InterruptedException {
        var request = HttpRequest.newBuilder(
                        URI.create("http://127.0.0.1:" + server.getAddress().getPort() + path))
                .timeout(Duration.ofSeconds(10))
                .method(method, body == null
                        ? HttpRequest.BodyPublishers.noBody()
                        : HttpRequest.BodyPublishers.ofString(body));
        if (type != null) {
            request.header("Content-Type", type);
        }
        return CLIENT.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    HttpResponse<String> get(String path) throws IOException, InterruptedException {
        return send("GET", path, null, null);
    }

    HttpResponse<String> post(String path, String body) throws IOException, InterruptedException {
        return send("POST", path, "application/json", body);
    }

    /** That the reply has the status, and a body of the media type with the same JSON. */
    static void assertReply(int status, String type, String json, HttpResponse<String> reply) {
        assertEquals(status, reply.statusCode(), reply.body());
        assertEquals(type, reply.headers().firstValue("Content-Type").orElse(null));
        assertEquals(JSON.readTree(json), JSON.readTree(reply.body()), reply.body());
    }

    static void assertProblem(int status, String title, String detail, HttpResponse<String> reply) {
        var detailed = detail == null ? "" : ",\"detail\":" + JSON.writeValueAsString(detail);
        assertReply(status, "application/problem+json",
                "{\"type\":\"about:blank\",\"title\":\"" + title + "\",\"status\":" + status + detailed + "}",
                reply);
    }

    static void assertUnfit(String detail, String pointer, HttpResponse<String> reply) {
        assertReply(422, "application/problem+json", """
                {"type":"about:blank","title":"Unprocessable Content","status":422,
                 "detail":"The request's content doesn't fit.",
                 "errors":[{"detail":%s,"pointer":%s}]}"""
                .formatted(JSON.writeValueAsString(detail), JSON.writeValueAsString(pointer)), reply);
    }

    @Test
    @DisplayName("tst_huudpt Lists the caller's tickets")
    void list() throws Exception {
        assertReply(200, "application/json", "[" + CARD_JSON + "," + ADDRESS_JSON + "]", get("/tickets"));
    }

    @Test
    @DisplayName("tst_wnvfw5 Opens a ticket, and says where it is")
    void open() throws Exception {
        var opened = post("/tickets", "{\"service\":\"va\",\"summary\":\" My GI Bill payment is late. \"}");
        var json = "{\"ticket\":\"T-3001\",\"service\":\"va\",\"status\":\"open\",\"summary\":\"My GI Bill payment is late.\"}";
        assertReply(201, "application/json", json, opened);
        assertEquals("/tickets/T-3001", opened.headers().firstValue("Location").orElse(null));
        assertReply(200, "application/json", json, get("/tickets/T-3001"));
        assertReply(200, "application/json", "[" + CARD_JSON + "," + ADDRESS_JSON + "," + json + "]", get("/tickets"));
    }

    @Test
    @DisplayName("tst_50yk3k Gives a ticket by its id, or a 404")
    void ticket() throws Exception {
        assertReply(200, "application/json", CARD_JSON, get("/tickets/T-2041"));
        assertProblem(404, "Not Found", "There's no ticket with this id.", get("/tickets/T-9"));
    }

    @Test
    @DisplayName("tst_gak05x Books a callback on a ticket")
    void book() throws Exception {
        assertReply(201, "application/json", "{\"ticket\":\"T-2041\",\"day\":\"2026-11-02\",\"time\":\"09:00\"}",
                post("/tickets/T-2041/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"09:00\"}"));
        assertEquals(List.of(new Desk.Callback("T-2041", MONDAY, LocalTime.of(9, 0))), desk.callbacks());
    }

    @Test
    @DisplayName("tst_6m6gzz Answers a booking the desk refuses with 409, and why")
    void refused() throws Exception {
        post("/tickets/T-2041/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"09:00\"}");
        assertProblem(409, "Conflict",
                "The advisers aren't free on Monday 2026-11-02 at 09:00. They're free at 10:00, 14:00.",
                post("/tickets/T-2041/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"09:00\"}"));
        assertProblem(409, "Conflict", "The caller has no open ticket T-1873.",
                post("/tickets/T-1873/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"10:00\"}"));
        assertProblem(404, "Not Found", "There's no ticket with this id.",
                post("/tickets/T-9/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"10:00\"}"));
    }

    @Test
    @DisplayName("tst_5u8kmq Refuses content that doesn't fit, saying where")
    void unfit() throws Exception {
        assertUnfit("The value doesn't fit this field.", "#/service",
                post("/tickets", "{\"service\":\"irs\",\"summary\":\"My refund is late.\"}"));
        assertUnfit("The value doesn't fit this field.", "#/summary", post("/tickets", "{\"service\":\"va\"}"));
        assertUnfit("There's no such field.", "#/urgent",
                post("/tickets", "{\"service\":\"va\",\"summary\":\"My GI Bill payment is late.\",\"urgent\":true}"));
        assertUnfit("The value doesn't fit this field.", "#/time",
                post("/tickets/T-2041/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"9:00\"}"));
        assertUnfit("The value doesn't fit this field.", "#/time",
                post("/tickets/T-2041/callbacks", "{\"day\":\"2026-11-02\",\"time\":\"09:00:30\"}"));
        assertProblem(400, "Bad Request", "The request's body isn't JSON.", post("/tickets", "{\"service\":"));
        // The API's mapper reads every request this way.
        assertThrows(JacksonException.class, () -> Api.JSON.readValue("{\"service\":\"va\"}", Api.NewTicket.class));
        assertThrows(JacksonException.class,
                () -> Api.JSON.readValue("{\"service\":\"va\",\"summary\":\"Late.\",\"urgent\":true}", Api.NewTicket.class));
    }

    @Test
    @DisplayName("tst_y3lfrb Refuses a summary the ticket refuses, and opens nothing")
    void summary() throws Exception {
        assertProblem(422, "Unprocessable Content", "A ticket's summary is a sentence about the case.",
                post("/tickets", "{\"service\":\"va\",\"summary\":\"   \"}"));
        assertEquals(List.of(CARD, ADDRESS), desk.tickets());
        assertEquals("/tickets/T-3001",
                post("/tickets", "{\"service\":\"va\",\"summary\":\"My GI Bill payment is late.\"}")
                        .headers().firstValue("Location").orElse(null));
    }

    @Test
    @DisplayName("tst_sablbn Answers an address it doesn't have with a 404")
    void nowhere() throws Exception {
        for (var path : List.of("/", "/ticketsX", "/tickets/", "/tickets/T-2041/callbacks/T-1", "/callbacks")) {
            assertProblem(404, "Not Found", null, get(path));
        }
    }

    @Test
    @DisplayName("tst_gg0x1o Answers a method an address doesn't take with a 405, and the ones it does")
    void methods() throws Exception {
        var reply = send("DELETE", "/tickets", null, null);
        assertProblem(405, "Method Not Allowed", null, reply);
        assertEquals("GET, POST", reply.headers().firstValue("Allow").orElse(null));
        reply = send("PUT", "/tickets/T-2041", "application/json", CARD_JSON);
        assertProblem(405, "Method Not Allowed", null, reply);
        assertEquals("GET", reply.headers().firstValue("Allow").orElse(null));
        reply = get("/tickets/T-2041/callbacks");
        assertProblem(405, "Method Not Allowed", null, reply);
        assertEquals("POST", reply.headers().firstValue("Allow").orElse(null));
    }

    @Test
    @DisplayName("tst_6bk0nr Takes a body only as application/json")
    void media() throws Exception {
        var summary = "{\"service\":\"va\",\"summary\":\"My GI Bill payment is late.\"}";
        var detail = "The desk reads a request's body as application/json.";
        assertProblem(415, "Unsupported Media Type", detail, send("POST", "/tickets", "text/plain", summary));
        assertProblem(415, "Unsupported Media Type", detail, send("POST", "/tickets", null, summary));
        assertProblem(415, "Unsupported Media Type", detail,
                send("POST", "/tickets/T-2041/callbacks", "application/x-www-form-urlencoded", "day=2026-11-02"));
        assertEquals(201, send("POST", "/tickets", "Application/JSON; charset=utf-8", summary).statusCode());
        assertEquals(List.of(CARD, ADDRESS, desk.tickets().get(2)), desk.tickets());
    }

    @Test
    @DisplayName("tst_d4wx9m Opens every ticket of many callers at once")
    void many() throws Exception {
        var replies = new ArrayList<java.util.concurrent.Future<HttpResponse<String>>>();
        try (var callers = Executors.newVirtualThreadPerTaskExecutor()) {
            for (var i = 0; i < 50; i++) {
                var summary = "Question " + i + " about my GI Bill payment.";
                replies.add(callers.submit(() -> post("/tickets", "{\"service\":\"va\",\"summary\":\"" + summary + "\"}")));
            }
        }
        var ids = new HashSet<String>();
        for (var reply : replies) {
            assertEquals(201, reply.get().statusCode(), reply.get().body());
            ids.add(JSON.readTree(reply.get().body()).get("ticket").asString());
        }
        assertEquals(50, ids.size());
        assertEquals(52, desk.tickets().size());
        assertEquals(52, JSON.readTree(get("/tickets").body()).size());
    }
}
