import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;

/** One caller's desk: their tickets and booked callbacks, and the advisers' free times by
 * service and day. */
public final class Desk {
    /** A callback booked on a ticket: the day and the time an adviser calls. */
    public record Callback(String ticket, LocalDate day, LocalTime time) {}

    /** A request the desk can't carry out, saying why, and what the caller can do instead. */
    public static final class Refused extends Exception {
        public Refused(String message) {
            super(message);
        }
    }

    public Desk(List<Ticket> tickets, Map<Service, Map<LocalDate, List<LocalTime>>> free) {}

    /** The caller's tickets, in the order the desk was given them and opened them. */
    public List<Ticket> tickets() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The callbacks booked, in the order they were booked. */
    public List<Callback> callbacks() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The times the service's advisers are free on the day, in order. */
    public List<LocalTime> free(Service service, LocalDate day) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The caller's tickets with the status, as the desk lists them, and how many have the
     * other. */
    public String listTickets(Ticket.Status status) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Opens a ticket for an adviser of the service, and gives it. */
    public Ticket openTicket(Service service, String summary) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Books an adviser of the ticket's service to call at a time they're free, and gives the
     * callback. */
    public Callback bookCallback(String ticket, LocalDate day, LocalTime time) throws Refused {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Cancels a booked callback, and frees its time for the ticket's service. */
    public void cancelCallback(String ticket, LocalDate day, LocalTime time) throws Refused {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
