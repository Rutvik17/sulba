import java.time.LocalDate;
import java.util.List;

/** The tools a model calls, each by its name, with its arguments written as JSON text. */
public final class Tools {
    /** What a tool does with its arguments, giving the text the model reads. */
    @FunctionalInterface
    public interface Action<A> {
        String run(A arguments) throws Desk.Refused;
    }

    /** A tool: its name, the record its arguments are read into, an example of them as JSON,
     * and what it does. */
    public record Tool<A extends Record>(String name, Class<A> arguments, String example, Action<A> action) {}

    /** list_tickets's arguments. */
    public record ListTickets(Ticket.Status status) {}

    /** free_times's arguments. */
    public record FreeTimes(Service service, LocalDate day) {}

    public Tools(List<Tool<?>> tools) {}

    /** The desk's tools for a model: list_tickets and free_times. */
    public static Tools forDesk(Desk desk) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The tools' names, in the order they were given. */
    public List<String> names() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Runs the tool a model called, with the arguments it wrote, and gives the text the model
     * reads: the tool's result, or an error that says how to call again. */
    public String call(String name, String arguments) {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
