import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.DatabindException;
import tools.jackson.databind.json.JsonMapper;

class TicketTest {
    static final JsonMapper JSON = JsonMapper.builder().build();
    static final String CARD = "My replacement Social Security card hasn't come.";

    static Ticket card() {
        return new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, CARD);
    }

    @Test
    @DisplayName("tst_9bu7fn Keeps its id, service, status and summary")
    void fields() {
        var ticket = card();
        assertEquals("T-2041", ticket.id());
        assertEquals(Service.SSA, ticket.service());
        assertEquals(Ticket.Status.OPEN, ticket.status());
        assertEquals(CARD, ticket.summary());
        assertTrue(ticket.isOpen());
    }

    @Test
    @DisplayName("tst_fzia2g Is a record, so two tickets with the same parts are equal")
    void record() {
        assertTrue(Ticket.class.isRecord(), "Ticket is a record");
        assertEquals(card(), card());
        assertEquals(card().hashCode(), card().hashCode());
    }

    @Test
    @DisplayName("tst_bltf4u Strips the space around its summary")
    void strips() {
        assertEquals(CARD, new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, "  " + CARD + "\n").summary());
    }

    @Test
    @DisplayName("tst_nskrwk Refuses an id that isn't T- and a number")
    void ids() {
        for (var id : new String[] {"2041", "T-", "t-2041", "T-20a1", "T-2041 ", "TT-2041"}) {
            var refused = assertThrows(
                    IllegalArgumentException.class,
                    () -> new Ticket(id, Service.SSA, Ticket.Status.OPEN, CARD),
                    "the id \"" + id + "\"");
            assertEquals(
                    "A ticket's id is T- and its number, like T-2041, not \"" + id + "\".", refused.getMessage());
        }
    }

    @Test
    @DisplayName("tst_d55kpp Refuses a blank summary, and one over 300 characters")
    void summaries() {
        var blank = assertThrows(
                IllegalArgumentException.class, () -> new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, " \t "));
        assertEquals("A ticket's summary is a sentence about the case.", blank.getMessage());
        var fits = new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, "a".repeat(300) + " ");
        assertEquals(300, fits.summary().length());
        var tooLong = assertThrows(
                IllegalArgumentException.class,
                () -> new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, "a".repeat(301)));
        assertEquals("A ticket's summary is at most 300 characters, not 301.", tooLong.getMessage());
    }

    @Test
    @DisplayName("tst_vjlpd6 Refuses a part that's null, naming it")
    void nulls() {
        assertEquals(
                "id",
                assertThrows(NullPointerException.class, () -> new Ticket(null, Service.SSA, Ticket.Status.OPEN, CARD))
                        .getMessage());
        assertEquals(
                "service",
                assertThrows(NullPointerException.class, () -> new Ticket("T-2041", null, Ticket.Status.OPEN, CARD))
                        .getMessage());
        assertEquals(
                "status",
                assertThrows(NullPointerException.class, () -> new Ticket("T-2041", Service.SSA, null, CARD))
                        .getMessage());
        assertEquals(
                "summary",
                assertThrows(NullPointerException.class, () -> new Ticket("T-2041", Service.SSA, Ticket.Status.OPEN, null))
                        .getMessage());
    }

    @Test
    @DisplayName("tst_9q0o3x Closes as a new ticket, and leaves itself open")
    void closes() {
        var open = card();
        var closed = open.closed();
        assertNotSame(open, closed);
        assertEquals(new Ticket("T-2041", Service.SSA, Ticket.Status.CLOSED, CARD), closed);
        assertFalse(closed.isOpen());
        assertTrue(open.isOpen());
    }

    @Test
    @DisplayName("tst_zwwsna Gives its line, with its service's name")
    void line() {
        assertEquals("T-2041: Social Security, " + CARD, card().line());
        assertEquals(
                "T-1873: New York State's DMV, My new address isn't on my license.",
                new Ticket("T-1873", Service.DMV, Ticket.Status.CLOSED, "My new address isn't on my license.").line());
    }

    @Test
    @DisplayName("tst_1y1mif Writes JSON with the desk's names")
    void writes() {
        assertEquals(
                "{\"ticket\":\"T-2041\",\"service\":\"ssa\",\"status\":\"open\",\"summary\":\"" + CARD + "\"}",
                JSON.writeValueAsString(card()));
        assertEquals("\"closed\"", JSON.writeValueAsString(Ticket.Status.CLOSED));
    }

    @Test
    @DisplayName("tst_woarqo Reads JSON with the desk's names")
    void reads() {
        var read = JSON.readValue(
                "{\"ticket\": \"T-1873\", \"service\": \"dmv\", \"status\": \"closed\","
                        + " \"summary\": \"My new address isn't on my license.\"}",
                Ticket.class);
        assertEquals(
                new Ticket("T-1873", Service.DMV, Ticket.Status.CLOSED, "My new address isn't on my license."), read);
    }

    @Test
    @DisplayName("tst_4vx4gu Refuses JSON with a bad id, as it refuses one in Java")
    void readsChecked() {
        var refused = assertThrows(
                DatabindException.class,
                () -> JSON.readValue(
                        "{\"ticket\": \"2041\", \"service\": \"ssa\", \"status\": \"open\", \"summary\": \"Lost.\"}",
                        Ticket.class));
        var cause = assertInstanceOf(IllegalArgumentException.class, refused.getCause());
        assertEquals("A ticket's id is T- and its number, like T-2041, not \"2041\".", cause.getMessage());
    }
}
