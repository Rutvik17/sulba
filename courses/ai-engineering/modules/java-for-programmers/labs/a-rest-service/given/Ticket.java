import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Objects;

/** One of the caller's tickets: its id, the service whose adviser looks into it, whether it's
 * open, and what it's about. */
public record Ticket(@JsonProperty("ticket") String id, Service service, Status status, String summary) {
    /** Whether a ticket is open, or closed. */
    public enum Status {
        @JsonProperty("open")
        OPEN,
        @JsonProperty("closed")
        CLOSED
    }

    public Ticket {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(service, "service");
        Objects.requireNonNull(status, "status");
        Objects.requireNonNull(summary, "summary");
        if (!id.matches("T-[0-9]+")) {
            throw new IllegalArgumentException(
                    "A ticket's id is T- and its number, like T-2041, not \"" + id + "\".");
        }
        summary = summary.strip();
        if (summary.isEmpty()) {
            throw new IllegalArgumentException("A ticket's summary is a sentence about the case.");
        }
        if (summary.length() > 300) {
            throw new IllegalArgumentException(
                    "A ticket's summary is at most 300 characters, not " + summary.length() + ".");
        }
    }

    /** Whether the ticket is open. */
    @JsonIgnore
    public boolean isOpen() {
        return status == Status.OPEN;
    }

    /** The ticket, closed. */
    public Ticket closed() {
        return new Ticket(id, service, Status.CLOSED, summary);
    }

    /** The ticket as the desk lists it: its id, its service and its summary. */
    public String line() {
        return id + ": " + service.title() + ", " + summary;
    }
}
