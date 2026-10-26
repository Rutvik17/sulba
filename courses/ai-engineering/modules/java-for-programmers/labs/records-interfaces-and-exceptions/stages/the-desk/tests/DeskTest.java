import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

class DeskTest {
    static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);
    static final LocalDate TUESDAY = LocalDate.of(2026, 11, 3);
    static final LocalTime NINE = LocalTime.of(9, 0);
    static final LocalTime TEN = LocalTime.of(10, 0);
    static final LocalTime TWO = LocalTime.of(14, 0);
    static final Ticket CARD = new Ticket(
            "T-2041", Service.SSA, Ticket.Status.OPEN, "My replacement Social Security card hasn't come.");
    static final Ticket ADDRESS =
            new Ticket("T-1873", Service.DMV, Ticket.Status.CLOSED, "My new address isn't on my license.");

    /** The advisers' free times: Social Security's on Monday at 14:00, 9:00 and 10:00, given out
     * of order, and the DMV's on Tuesday at 9:00. */
    static Map<Service, Map<LocalDate, List<LocalTime>>> free() {
        var free = new EnumMap<Service, Map<LocalDate, List<LocalTime>>>(Service.class);
        free.put(Service.SSA, new HashMap<>(Map.of(MONDAY, new ArrayList<>(List.of(TWO, NINE, TEN)))));
        free.put(Service.DMV, new HashMap<>(Map.of(TUESDAY, new ArrayList<>(List.of(NINE)))));
        return free;
    }

    static Desk desk() {
        return new Desk(List.of(CARD, ADDRESS), free());
    }

    @Test
    @DisplayName("tst_23r80z Keeps its own copies of what it's given")
    void copies() {
        var tickets = new ArrayList<>(List.of(CARD));
        var free = free();
        var desk = new Desk(tickets, free);
        tickets.add(ADDRESS);
        free.get(Service.SSA).get(MONDAY).clear();
        assertEquals(List.of(CARD), desk.tickets());
        assertEquals(List.of(NINE, TEN, TWO), desk.free(Service.SSA, MONDAY));
    }

    @Test
    @DisplayName("tst_6cnny7 Gives lists that can't change it")
    void readOnly() {
        var desk = desk();
        assertThrows(UnsupportedOperationException.class, () -> desk.tickets().clear());
        assertThrows(UnsupportedOperationException.class, () -> desk.callbacks().add(null));
        assertThrows(UnsupportedOperationException.class, () -> desk.free(Service.SSA, MONDAY).remove(NINE));
        assertEquals(List.of(CARD, ADDRESS), desk.tickets());
    }

    @Test
    @DisplayName("tst_vs7210 Gives each service's free times in order, and none for a day without")
    void freeTimes() {
        var desk = desk();
        assertEquals(List.of(NINE, TEN, TWO), desk.free(Service.SSA, MONDAY));
        assertEquals(List.of(), desk.free(Service.SSA, TUESDAY));
        assertEquals(List.of(), desk.free(Service.VA, MONDAY));
    }

    @Test
    @DisplayName("tst_t5bmn7 Lists the tickets with a status, and counts the others")
    void lists() {
        var desk = desk();
        assertEquals(
                "The caller's open tickets:\nT-2041: Social Security, My replacement Social Security card hasn't come."
                        + "\nThey have 1 closed ticket: list_tickets with status \"closed\" lists them.",
                desk.listTickets(Ticket.Status.OPEN));
        assertEquals(
                "The caller's closed tickets:\nT-1873: New York State's DMV, My new address isn't on my license."
                        + "\nThey have 1 open ticket: list_tickets with status \"open\" lists them.",
                desk.listTickets(Ticket.Status.CLOSED));
    }

    @Test
    @DisplayName("tst_qsnhnu Says when there are none, and counts others in the plural")
    void listsNone() {
        var desk = new Desk(List.of(ADDRESS, new Ticket("T-1870", Service.VA, Ticket.Status.CLOSED, "Done.")), free());
        assertEquals(
                "The caller has no open tickets."
                        + "\nThey have 2 closed tickets: list_tickets with status \"closed\" lists them.",
                desk.listTickets(Ticket.Status.OPEN));
        assertEquals("The caller has no open tickets.", new Desk(List.of(), free()).listTickets(Ticket.Status.OPEN));
    }

    @Test
    @DisplayName("tst_i2mrq1 Opens tickets from T-3001, and lists them")
    void opens() {
        var desk = desk();
        var first = desk.openTicket(Service.VA, "  My claim hasn't moved. ");
        assertEquals(new Ticket("T-3001", Service.VA, Ticket.Status.OPEN, "My claim hasn't moved."), first);
        assertEquals("T-3002", desk.openTicket(Service.DMV, "My plates.").id());
        assertEquals(List.of("T-2041", "T-1873", "T-3001", "T-3002"),
                desk.tickets().stream().map(Ticket::id).toList());
    }

    @Test
    @DisplayName("tst_dnxce3 Opens no ticket, and uses no number, for a summary the ticket refuses")
    void opensChecked() {
        var desk = desk();
        assertThrows(IllegalArgumentException.class, () -> desk.openTicket(Service.VA, " "));
        assertEquals(2, desk.tickets().size());
        assertEquals("T-3001", desk.openTicket(Service.VA, "My claim hasn't moved.").id());
    }

    @Test
    @DisplayName("tst_g4cyb3 Books a callback at a free time, which is then taken")
    void books() throws Desk.Refused {
        var desk = desk();
        var callback = desk.bookCallback("T-2041", MONDAY, TEN);
        assertEquals(new Desk.Callback("T-2041", MONDAY, TEN), callback);
        assertEquals(List.of(callback), desk.callbacks());
        assertEquals(List.of(NINE, TWO), desk.free(Service.SSA, MONDAY));
    }

    @Test
    @DisplayName("tst_533vq7 Refuses a callback on a ticket that isn't open")
    void booksOnOpen() {
        var desk = desk();
        assertEquals(
                "The caller has no open ticket T-1873.",
                assertThrows(Desk.Refused.class, () -> desk.bookCallback("T-1873", TUESDAY, NINE)).getMessage());
        assertEquals(
                "The caller has no open ticket T-9.",
                assertThrows(Desk.Refused.class, () -> desk.bookCallback("T-9", MONDAY, NINE)).getMessage());
        assertEquals(List.of(), desk.callbacks());
    }

    @Test
    @DisplayName("tst_j33m3j Refuses a time the advisers aren't free, saying when they are")
    void booksFree() throws Desk.Refused {
        var desk = desk();
        assertEquals(
                "The advisers aren't free on Monday 2026-11-02 at 11:00. They're free at 09:00, 10:00, 14:00.",
                assertThrows(Desk.Refused.class, () -> desk.bookCallback("T-2041", MONDAY, LocalTime.of(11, 0)))
                        .getMessage());
        assertEquals(
                "The advisers aren't free on Tuesday 2026-11-03 at 09:00. They're free at no time that day.",
                assertThrows(Desk.Refused.class, () -> desk.bookCallback("T-2041", TUESDAY, NINE)).getMessage());
        desk.bookCallback("T-2041", MONDAY, NINE);
        assertThrows(Desk.Refused.class, () -> desk.bookCallback("T-2041", MONDAY, NINE));
        assertEquals(1, desk.callbacks().size());
    }

    @Test
    @DisplayName("tst_udo0ly Cancels a callback, and frees its time again, in order")
    void cancels() throws Desk.Refused {
        var desk = desk();
        desk.bookCallback("T-2041", MONDAY, NINE);
        desk.bookCallback("T-2041", MONDAY, TEN);
        desk.cancelCallback("T-2041", MONDAY, NINE);
        assertEquals(List.of(new Desk.Callback("T-2041", MONDAY, TEN)), desk.callbacks());
        assertEquals(List.of(NINE, TWO), desk.free(Service.SSA, MONDAY));
        assertEquals(
                "The caller has no callback about T-2041 on 2026-11-02 at 09:00.",
                assertThrows(Desk.Refused.class, () -> desk.cancelCallback("T-2041", MONDAY, NINE)).getMessage());
    }

    @Test
    @DisplayName("tst_jg0ejn Refuses with a checked exception, which a caller has to handle")
    void checked() {
        assertTrue(Exception.class.isAssignableFrom(Desk.Refused.class));
        assertFalse(RuntimeException.class.isAssignableFrom(Desk.Refused.class));
    }

    @Test
    @DisplayName("tst_dfpb7c Writes a callback as JSON, with its time in hours and minutes")
    void json() throws Desk.Refused {
        var callback = desk().bookCallback("T-2041", MONDAY, NINE);
        assertEquals(
                "{\"ticket\":\"T-2041\",\"day\":\"2026-11-02\",\"time\":\"09:00\"}",
                JsonMapper.builder().build().writeValueAsString(callback));
    }
}
