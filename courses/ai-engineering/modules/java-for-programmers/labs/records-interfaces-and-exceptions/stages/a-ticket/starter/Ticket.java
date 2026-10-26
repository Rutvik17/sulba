/** One of the caller's tickets: its id, the service whose adviser looks into it, whether it's
 * open, and what it's about. */
public record Ticket(String id, Service service, Status status, String summary) {
    /** Whether a ticket is open, or closed. */
    public enum Status {
        OPEN,
        CLOSED
    }

    /** Whether the ticket is open. */
    public boolean isOpen() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The ticket, closed. */
    public Ticket closed() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The ticket as the desk lists it: its id, its service and its summary. */
    public String line() {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
