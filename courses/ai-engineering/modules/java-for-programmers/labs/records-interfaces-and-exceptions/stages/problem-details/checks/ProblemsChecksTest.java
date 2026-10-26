import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.json.JsonMapper;

class ProblemsChecksTest {
    static final JsonMapper JSON = JsonMapper.builder().build();

    /** A record Jackson can't make, since an interface can't be read from JSON: the code's
     * mistake, not the request's. */
    record Job(Runnable task) {}

    @Test
    @DisplayName("tst_wyqiqg Nothing inside leaks")
    void nothingLeaks() {
        var secret = Problems.of(new IllegalStateException("Connecting to postgres://desk:hunter2@db failed."));
        assertNull(secret.detail());
        assertFalse(Problems.json(secret).contains("hunter2"));
        var definition = assertThrows(JacksonException.class, () -> JSON.readValue("{\"task\": {}}", Job.class));
        var problem = Problems.of(definition);
        assertEquals(500, problem.status());
        assertNull(problem.detail());
        assertNull(problem.errors());
    }

    @Test
    @DisplayName("tst_3lwewo Each status's own title")
    void titles() {
        var titles = Map.of(
                400, "Bad Request",
                404, "Not Found",
                405, "Method Not Allowed",
                409, "Conflict",
                413, "Content Too Large",
                415, "Unsupported Media Type",
                422, "Unprocessable Content",
                429, "Too Many Requests",
                500, "Internal Server Error",
                503, "Service Unavailable");
        titles.forEach((status, title) -> assertEquals(title, Problems.of(status, null).title(), "status " + status));
    }

    @Test
    @DisplayName("tst_0ghv7v A pointer for any key")
    void pointers() {
        assertEquals("#/a~1b/m~0n", Problems.pointer(List.of("a/b", "m~n")));
        assertEquals("#/what%20for/50%25", Problems.pointer(List.of("what for", "50%")));
        assertEquals("#/caf%C3%A9/%22quoted%22/%23/a?b=c", Problems.pointer(List.of("café", "\"quoted\"", "#", "a?b=c")));
        assertEquals("#/%7Bx%7D/%5B0%5D/0", Problems.pointer(List.of("{x}", "[0]", 0)));
    }

    @Test
    @DisplayName("tst_cn0olo However deep the error is wrapped")
    void wrapped() {
        var refused = new Desk.Refused("The caller has no callback about T-2041 on 2026-11-02 at 09:00.");
        assertEquals(
                Problems.of(409, refused.getMessage()),
                Problems.of(new CompletionException(new RuntimeException(new IllegalStateException(refused)))));
        var unfit = assertThrows(JacksonException.class, () -> JSON.readValue("{\"day\": \"Monday\"}", Asked.class));
        var problem = Problems.of(new ExecutionException(new RuntimeException(unfit)));
        assertEquals(422, problem.status());
        assertEquals(List.of(new Problems.Invalid("The value doesn't fit this field.", "#/day")), problem.errors());
    }

    record Asked(java.time.LocalDate day) {}
}
