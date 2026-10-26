import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.json.JsonMapper;

class ProblemsTest {
    /** A mapper that reads requests as the desk's API does, refusing a field its record lacks. */
    static final JsonMapper JSON =
            JsonMapper.builder().enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES).build();
    static final String UNFIT = "The request's content doesn't fit.";

    /** What a request's JSON can hold: tickets, read into Ticket records. */
    record Batch(List<Ticket> tickets) {}

    /** The error Jackson gives reading the text into a Batch. */
    static JacksonException reading(String text) {
        return assertThrows(JacksonException.class, () -> JSON.readValue(text, Batch.class));
    }

    @Test
    @DisplayName("tst_iv4adp Makes a problem of type about:blank, titled for its status")
    void of() {
        assertEquals(
                new Problems.Problem("about:blank", "Not Found", 404, "There's no conversation with this id.", null),
                Problems.of(404, "There's no conversation with this id."));
        assertEquals(new Problems.Problem("about:blank", "Conflict", 409, null, null), Problems.of(409, null));
    }

    @Test
    @DisplayName("tst_ssdajy Refuses a status the desk doesn't answer with")
    void statuses() {
        assertThrows(IllegalArgumentException.class, () -> Problems.of(418, null));
    }

    @Test
    @DisplayName("tst_m0djmk Writes JSON without a detail or errors it doesn't have")
    void json() {
        assertEquals(
                "{\"type\":\"about:blank\",\"title\":\"Bad Request\",\"status\":400,\"detail\":\"No.\"}",
                Problems.json(Problems.of(400, "No.")));
        assertEquals(
                "{\"type\":\"about:blank\",\"title\":\"Internal Server Error\",\"status\":500}",
                Problems.json(Problems.of(500, null)));
        assertEquals("application/problem+json", Problems.MEDIA_TYPE);
    }

    @Test
    @DisplayName("tst_p9t2wk Answers a refusal with 409 and its message")
    void refused() {
        var problem = Problems.of(new Desk.Refused("The caller has no open ticket T-9."));
        assertEquals(Problems.of(409, "The caller has no open ticket T-9."), problem);
    }

    @Test
    @DisplayName("tst_k1tpwy Answers a value that doesn't fit with 422, and where it is")
    void unfit() {
        var problem = Problems.of(reading(
                "{\"tickets\": [{\"ticket\": \"T-1\", \"service\": \"ssa\", \"status\": \"open\", \"summary\": \"A.\"},"
                        + " {\"ticket\": \"T-2\", \"service\": \"irs\", \"status\": \"open\", \"summary\": \"B.\"}]}"));
        assertEquals(422, problem.status());
        assertEquals("Unprocessable Content", problem.title());
        assertEquals(UNFIT, problem.detail());
        assertEquals(
                List.of(new Problems.Invalid("The value doesn't fit this field.", "#/tickets/1/service")),
                problem.errors());
    }

    @Test
    @DisplayName("tst_nlcevy Gives a record's own refusal as the error's detail")
    void refusedByRecord() {
        var problem = Problems.of(reading(
                "{\"tickets\": [{\"ticket\": \"2041\", \"service\": \"ssa\", \"status\": \"open\", \"summary\": \"A.\"}]}"));
        assertEquals(
                List.of(new Problems.Invalid(
                        "A ticket's id is T- and its number, like T-2041, not \"2041\".", "#/tickets/0")),
                problem.errors());
    }

    @Test
    @DisplayName("tst_owxo9t Names a field the request has that its record doesn't")
    void unknownField() {
        assertEquals(
                List.of(new Problems.Invalid("There's no such field.", "#/ticket")),
                Problems.of(reading("{\"ticket\": \"T-2041\"}")).errors());
    }

    @Test
    @DisplayName("tst_ftevnl Answers a body that isn't JSON with 400")
    void notJson() {
        assertEquals(Problems.of(400, "The request's body isn't JSON."), Problems.of(reading("{\"tickets\": [")));
    }

    @Test
    @DisplayName("tst_rxmx1c Answers anything else with 500, and no detail")
    void anythingElse() {
        assertEquals(Problems.of(500, null), Problems.of(new IllegalStateException("The desk broke.")));
    }

    @Test
    @DisplayName("tst_pyitmj Points at the whole document, a key and an index")
    void pointers() {
        assertEquals("#", Problems.pointer(List.of()));
        assertEquals("#/tickets/1/service", Problems.pointer(List.of("tickets", 1, "service")));
    }
}
