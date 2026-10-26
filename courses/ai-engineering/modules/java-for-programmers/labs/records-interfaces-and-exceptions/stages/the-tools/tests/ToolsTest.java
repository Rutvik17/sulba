import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class ToolsTest {
    static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);
    static final Ticket CARD = new Ticket(
            "T-2041", Service.SSA, Ticket.Status.OPEN, "My replacement Social Security card hasn't come.");
    static final Ticket ADDRESS =
            new Ticket("T-1873", Service.DMV, Ticket.Status.CLOSED, "My new address isn't on my license.");
    static final String LIST = "{\"status\": \"open\"}";
    static final String FREE = "{\"service\": \"ssa\", \"day\": \"2026-11-03\"}";

    static Desk desk() {
        return new Desk(
                List.of(CARD, ADDRESS),
                Map.of(Service.SSA, Map.of(MONDAY, List.of(LocalTime.of(14, 0), LocalTime.of(9, 0)))));
    }

    /** A tool of the test's own: its arguments, read into a record, and what it does. */
    record Repeat(String text, int times) {}

    static final Tools.Tool<Repeat> REPEAT = new Tools.Tool<>(
            "repeat", Repeat.class, "{\"text\": \"hi\", \"times\": 2}", arguments -> arguments.text()
                    .repeat(arguments.times()));

    /** A record that refuses a value in its constructor. */
    record Note(String text) {
        Note {
            if (text.isBlank()) {
                throw new IllegalArgumentException("text is a sentence for the note.");
            }
        }
    }

    @Test
    @DisplayName("tst_09brwu Gives the desk's two tools, list_tickets and free_times")
    void names() {
        assertEquals(List.of("list_tickets", "free_times"), Tools.forDesk(desk()).names());
    }

    @Test
    @DisplayName("tst_ctp10v Runs list_tickets with the status it's given")
    void listTickets() {
        var tools = Tools.forDesk(desk());
        assertEquals(desk().listTickets(Ticket.Status.OPEN), tools.call("list_tickets", LIST));
        assertEquals(desk().listTickets(Ticket.Status.CLOSED), tools.call("list_tickets", "{\"status\": \"closed\"}"));
    }

    @Test
    @DisplayName("tst_diwxg5 Runs free_times, with the service's name and the day")
    void freeTimes() {
        var tools = Tools.forDesk(desk());
        assertEquals(
                "The Social Security advisers are free on Monday 2026-11-02 at 09:00, 14:00.",
                tools.call("free_times", "{\"service\": \"ssa\", \"day\": \"2026-11-02\"}"));
        assertEquals(
                "The veterans' benefits advisers aren't free on Monday 2026-11-02.",
                tools.call("free_times", "{\"day\": \"2026-11-02\", \"service\": \"va\"}"));
    }

    @Test
    @DisplayName("tst_crtmoq Runs a tool of any record, with its own arguments")
    void anyTool() {
        var tools = new Tools(List.of(REPEAT));
        assertEquals(List.of("repeat"), tools.names());
        assertEquals("hohoho", tools.call("repeat", "{\"text\": \"ho\", \"times\": 3}"));
    }

    @Test
    @DisplayName("tst_t0peci Names the tools when there's none by the name called")
    void unknown() {
        assertEquals(
                "Error: there is no tool named \"book\". The tools are list_tickets, free_times.",
                Tools.forDesk(desk()).call("book", LIST));
    }

    @Test
    @DisplayName("tst_y50rpy Asks for one JSON object, with the tool's example")
    void notAnObject() {
        var tools = Tools.forDesk(desk());
        var expected =
                "Error: list_tickets's arguments are one JSON object, like {\"status\": \"open\"}, and these aren't.";
        for (var arguments : new String[] {"{\"status\": ", "[\"open\"]", "\"open\"", "open", "null"}) {
            assertEquals(expected, tools.call("list_tickets", arguments), arguments);
        }
    }

    @Test
    @DisplayName("tst_1asqm2 Asks for each argument the record has, given as null or not at all")
    void missing() {
        var tools = Tools.forDesk(desk());
        assertEquals(
                "Error: list_tickets needs status. For example: {\"status\": \"open\"}", tools.call("list_tickets", ""));
        assertEquals(
                "Error: free_times needs day. For example: " + FREE,
                tools.call("free_times", "{\"service\": \"ssa\", \"day\": null}"));
        assertEquals(
                "Error: free_times needs service. For example: " + FREE, tools.call("free_times", "{}"));
    }

    @Test
    @DisplayName("tst_4q6ar3 Refuses an argument the record doesn't have, naming those it does")
    void unknownArgument() {
        assertEquals(
                "Error: free_times takes no time. It takes service, day, like " + FREE + ".",
                Tools.forDesk(desk())
                        .call("free_times", "{\"service\": \"ssa\", \"day\": \"2026-11-02\", \"time\": \"09:00\"}"));
    }

    @Test
    @DisplayName("tst_cgk79e Refuses a value its field can't hold, quoting it")
    void wrongValue() {
        var tools = Tools.forDesk(desk());
        assertEquals(
                "Error: status can't be \"pending\". For example: " + LIST,
                tools.call("list_tickets", "{\"status\": \"pending\"}"));
        assertEquals(
                "Error: day can't be \"Monday\". For example: " + FREE,
                tools.call("free_times", "{\"service\": \"ssa\", \"day\": \"Monday\"}"));
        assertEquals(
                "Error: service can't be \"irs\". For example: " + FREE,
                tools.call("free_times", "{\"service\": \"irs\", \"day\": \"2026-11-02\"}"));
        assertEquals(
                "Error: times can't be \"lots\". For example: {\"text\": \"hi\", \"times\": 2}",
                new Tools(List.of(REPEAT)).call("repeat", "{\"text\": \"ho\", \"times\": \"lots\"}"));
    }

    @Test
    @DisplayName("tst_vxn6fq Gives a record's own refusal, and a desk's, as the error")
    void refusals() {
        var desk = desk();
        var tools = new Tools(List.of(
                new Tools.Tool<>("note", Note.class, "{\"text\": \"Called back.\"}", note -> "Noted."),
                new Tools.Tool<>(
                        "book_monday_nine",
                        Tools.ListTickets.class,
                        LIST,
                        arguments -> desk.bookCallback("T-1873", MONDAY, LocalTime.of(9, 0)).toString())));
        assertEquals("Error: text is a sentence for the note.", tools.call("note", "{\"text\": \" \"}"));
        assertEquals("Error: The caller has no open ticket T-1873.", tools.call("book_monday_nine", LIST));
    }

    @Test
    @DisplayName("tst_zghsjp Lets a tool's own bug through, rather than hand it to the model")
    void bugs() {
        var tools = new Tools(List.of(new Tools.Tool<>("broken", Tools.ListTickets.class, LIST, arguments -> {
            throw new IllegalStateException("A bug in the tool.");
        })));
        assertThrows(IllegalStateException.class, () -> tools.call("broken", LIST));
    }

    @Test
    @DisplayName("tst_qq36u9 Refuses two tools with one name")
    void twoNames() {
        var refused = assertThrows(IllegalArgumentException.class, () -> new Tools(List.of(REPEAT, REPEAT)));
        assertEquals("Two tools are named repeat.", refused.getMessage());
    }
}
