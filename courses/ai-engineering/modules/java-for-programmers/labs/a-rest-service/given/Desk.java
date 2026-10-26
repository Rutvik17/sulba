import com.fasterxml.jackson.annotation.JsonFormat;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.stream.Collectors;

/** One caller's desk: their tickets and booked callbacks, and the advisers' free times by
 * service and day. */
public final class Desk {
    /** A callback booked on a ticket: the day and the time an adviser calls. */
    public record Callback(String ticket, LocalDate day, @JsonFormat(pattern = "HH:mm") LocalTime time) {
        public Callback {
            Objects.requireNonNull(ticket, "ticket");
            Objects.requireNonNull(day, "day");
            Objects.requireNonNull(time, "time");
        }
    }

    /** A request the desk can't carry out, saying why, and what the caller can do instead. */
    public static final class Refused extends Exception {
        public Refused(String message) {
            super(message);
        }
    }

    private final List<Ticket> tickets;
    private final Map<Service, Map<LocalDate, TreeSet<LocalTime>>> free = new EnumMap<>(Service.class);
    private final List<Callback> callbacks = new ArrayList<>();
    private int opened;

    public Desk(List<Ticket> tickets, Map<Service, Map<LocalDate, List<LocalTime>>> free) {
        this.tickets = new ArrayList<>(tickets);
        free.forEach((service, days) -> {
            var copy = new TreeMap<LocalDate, TreeSet<LocalTime>>();
            days.forEach((day, times) -> copy.put(day, new TreeSet<>(times)));
            this.free.put(service, copy);
        });
    }

    /** The caller's tickets, in the order the desk was given them and opened them. */
    public List<Ticket> tickets() {
        return List.copyOf(tickets);
    }

    /** The callbacks booked, in the order they were booked. */
    public List<Callback> callbacks() {
        return List.copyOf(callbacks);
    }

    /** The times the service's advisers are free on the day, in order. */
    public List<LocalTime> free(Service service, LocalDate day) {
        return List.copyOf(times(service, day));
    }

    /** The caller's tickets with the status, as the desk lists them, and how many have the
     * other. */
    public String listTickets(Ticket.Status status) {
        var other = status == Ticket.Status.OPEN ? Ticket.Status.CLOSED : Ticket.Status.OPEN;
        var mine = tickets.stream().filter(ticket -> ticket.status() == status).toList();
        var rest = tickets.stream().filter(ticket -> ticket.status() == other).count();
        var shown = mine.isEmpty()
                ? "The caller has no " + word(status) + " tickets."
                : "The caller's " + word(status) + " tickets:\n"
                        + mine.stream().map(Ticket::line).collect(Collectors.joining("\n"));
        if (rest > 0) {
            shown += "\nThey have " + rest + " " + word(other) + " ticket" + (rest > 1 ? "s" : "")
                    + ": list_tickets with status \"" + word(other) + "\" lists them.";
        }
        return shown;
    }

    /** Opens a ticket for an adviser of the service, and gives it. */
    public Ticket openTicket(Service service, String summary) {
        var ticket = new Ticket("T-" + (3001 + opened), service, Ticket.Status.OPEN, summary);
        opened++;
        tickets.add(ticket);
        return ticket;
    }

    /** Books an adviser of the ticket's service to call at a time they're free, and gives the
     * callback. */
    public Callback bookCallback(String ticket, LocalDate day, LocalTime time) throws Refused {
        var found = tickets.stream()
                .filter(each -> each.id().equals(ticket) && each.isOpen())
                .findFirst()
                .orElseThrow(() -> new Refused("The caller has no open ticket " + ticket + "."));
        var times = times(found.service(), day);
        if (!times.contains(time)) {
            var listed = times.stream().map(LocalTime::toString).collect(Collectors.joining(", "));
            throw new Refused("The advisers aren't free on " + weekday(day) + " " + day + " at " + time
                    + ". They're free at " + (listed.isEmpty() ? "no time that day" : listed) + ".");
        }
        times.remove(time);
        var callback = new Callback(ticket, day, time);
        callbacks.add(callback);
        return callback;
    }

    /** Cancels a booked callback, and frees its time for the ticket's service. */
    public void cancelCallback(String ticket, LocalDate day, LocalTime time) throws Refused {
        if (!callbacks.remove(new Callback(ticket, day, time))) {
            throw new Refused("The caller has no callback about " + ticket + " on " + day + " at " + time + ".");
        }
        var service = tickets.stream()
                .filter(each -> each.id().equals(ticket))
                .findFirst()
                .orElseThrow()
                .service();
        free.computeIfAbsent(service, key -> new TreeMap<>())
                .computeIfAbsent(day, key -> new TreeSet<>())
                .add(time);
    }

    private TreeSet<LocalTime> times(Service service, LocalDate day) {
        return free.getOrDefault(service, Map.of()).getOrDefault(day, new TreeSet<>());
    }

    private static String word(Ticket.Status status) {
        return status == Ticket.Status.OPEN ? "open" : "closed";
    }

    private static String weekday(LocalDate day) {
        return day.getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH);
    }
}
