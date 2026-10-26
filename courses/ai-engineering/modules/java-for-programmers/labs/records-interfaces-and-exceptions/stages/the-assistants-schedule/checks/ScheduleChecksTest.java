import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

class ScheduleChecksTest {
    static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);
    static final LocalDate TUESDAY = LocalDate.of(2026, 11, 3);
    static final LocalDate WEDNESDAY = LocalDate.of(2026, 11, 4);

    record Asked(String ticket) {}

    @Test
    @DisplayName("tst_xsn849 A ticket's bookings, by an id read from a request")
    void ids() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        var booking = schedule.book("T-2041", MONDAY, 2);
        var asked = JsonMapper.builder().build().readValue("{\"ticket\": \"T-2041\"}", Asked.class);
        assertEquals(List.of(booking), schedule.bookingsFor(asked.ticket()));
        assertEquals(List.of(booking), schedule.bookingsFor("T-" + Integer.parseInt("2041")));
    }

    @Test
    @DisplayName("tst_h8imi6 Two bookings on one day")
    void twoOnOneDay() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        schedule.book("T-2041", MONDAY, 2);
        schedule.book("T-3001", MONDAY, 5);
        assertEquals(List.of(0, 1, 3, 4, 6, 7), schedule.free(MONDAY));
        assertThrows(IllegalArgumentException.class, () -> schedule.book("T-3002", MONDAY, 5));
        schedule.book("T-3002", MONDAY, 7);
        assertEquals(List.of(0, 1, 3, 4, 6), schedule.free(MONDAY));
    }

    @Test
    @DisplayName("tst_i5xeat The bookings, as they were made, after a report sorts them")
    void bookingsStay() {
        var schedule = new Schedule();
        schedule.open(MONDAY);
        schedule.open(TUESDAY);
        var first = schedule.book("T-2041", TUESDAY, 2);
        var second = schedule.book("T-3001", MONDAY, 7);
        var report = schedule.bookings();
        try {
            report.sort(Comparator.comparing(Schedule.Booking::day));
        } catch (UnsupportedOperationException refused) {
            // A list that can't be sorted keeps the schedule's order too.
        }
        assertEquals(List.of(first, second), schedule.bookings());
    }

    @Test
    @DisplayName("tst_o6btc5 The open days, in the calendar's order")
    void days() {
        var schedule = new Schedule();
        schedule.open(WEDNESDAY);
        schedule.open(MONDAY);
        schedule.open(TUESDAY);
        assertEquals(List.of(MONDAY, TUESDAY, WEDNESDAY), schedule.days());
    }
}
