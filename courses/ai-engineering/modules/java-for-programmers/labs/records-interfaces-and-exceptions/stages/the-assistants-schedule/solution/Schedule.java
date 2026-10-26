import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** One service's advisers' week: the slots they're free in on each day they work, an hour each
 * from 09:00, and the callbacks booked into them. */
public final class Schedule {
    /** A callback booked into a slot of a day. */
    public record Booking(String ticket, LocalDate day, int slot) {
        /** The time the slot starts: slot 0 is 09:00, and slot 7 is 16:00. */
        public LocalTime time() {
            return LocalTime.of(9 + slot, 0);
        }
    }

    private final Map<LocalDate, List<Integer>> free = new HashMap<>();
    private final List<Booking> bookings = new ArrayList<>();

    /** Opens a day for callbacks, with its eight slots free. */
    public void open(LocalDate day) {
        var slots = new ArrayList<Integer>();
        for (var slot = 0; slot < 8; slot++) {
            slots.add(slot);
        }
        free.put(day, slots);
    }

    /** The days open for callbacks, in order. */
    public List<LocalDate> days() {
        return free.keySet().stream().sorted().toList();
    }

    /** The day's free slots, in order. */
    public List<Integer> free(LocalDate day) {
        return List.copyOf(free.getOrDefault(day, List.of()));
    }

    /** Books the ticket's callback into a free slot, and gives the booking. */
    public Booking book(String ticket, LocalDate day, int slot) {
        var slots = free.get(day);
        if (slots == null || !slots.contains(slot)) {
            throw new IllegalArgumentException("Slot " + slot + " on " + day + " isn't free.");
        }
        slots.remove(Integer.valueOf(slot));
        var booking = new Booking(ticket, day, slot);
        bookings.add(booking);
        return booking;
    }

    /** The ticket's bookings, in the order they were made. */
    public List<Booking> bookingsFor(String ticket) {
        return bookings.stream().filter(booking -> booking.ticket().equals(ticket)).toList();
    }

    /** Every booking, in the order they were made. */
    public List<Booking> bookings() {
        return List.copyOf(bookings);
    }
}
