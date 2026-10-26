import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class ScheduleTest {
    static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);
    static final LocalDate TUESDAY = LocalDate.of(2026, 11, 3);

    @Test
    @DisplayName("tst_4y9hzh Opens a day with its eight slots free")
    void opens() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        assertEquals(List.of(MONDAY), schedule.days());
        assertEquals(List.of(0, 1, 2, 3, 4, 5, 6, 7), schedule.free(MONDAY));
        assertEquals(List.of(), schedule.free(TUESDAY));
    }

    @Test
    @DisplayName("tst_1a3k7b Books a free slot, which is then taken")
    void books() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        var booking = schedule.book("T-2041", MONDAY, 3);
        assertEquals(new Schedule.Booking("T-2041", MONDAY, 3), booking);
        assertEquals(LocalTime.of(12, 0), booking.time());
        assertEquals(List.of(0, 1, 2, 4, 5, 6, 7), schedule.free(MONDAY));
    }

    @Test
    @DisplayName("tst_ufpcdf Refuses a slot that's taken, or on a day that isn't open")
    void refuses() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        schedule.book("T-2041", MONDAY, 3);
        assertThrows(IllegalArgumentException.class, () -> schedule.book("T-3001", MONDAY, 3));
        assertThrows(IllegalArgumentException.class, () -> schedule.book("T-3001", TUESDAY, 3));
        assertEquals(1, schedule.bookings().size());
    }

    @Test
    @DisplayName("tst_pv7y2b Gives a ticket's bookings")
    void bookingsFor() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        schedule.open(TUESDAY);
        var first = schedule.book("T-2041", MONDAY, 0);
        schedule.book("T-3001", MONDAY, 1);
        var second = schedule.book("T-2041", TUESDAY, 6);
        assertEquals(List.of(first, second), schedule.bookingsFor("T-2041"));
        assertEquals(List.of(), schedule.bookingsFor("T-9"));
    }

    @Test
    @DisplayName("tst_t7km0o Gives every booking, in the order they were made")
    void bookings() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        schedule.open(TUESDAY);
        var first = schedule.book("T-2041", TUESDAY, 2);
        var second = schedule.book("T-3001", MONDAY, 7);
        assertEquals(List.of(first, second), schedule.bookings());
    }
}
