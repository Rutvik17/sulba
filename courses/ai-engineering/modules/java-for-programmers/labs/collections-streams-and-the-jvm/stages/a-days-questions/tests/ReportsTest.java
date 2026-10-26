import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.SortedMap;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class ReportsTest {
    static final ZoneId NEW_YORK = ZoneId.of("America/New_York");

    static Reports.Asked asked(String at, Service service, String page, long seconds) {
        return new Reports.Asked(Instant.parse(at), service, page, Duration.ofSeconds(seconds));
    }

    /** Monday's questions, in the order they were asked. */
    static final List<Reports.Asked> MONDAY = List.of(
            asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4),
            asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9),
            asked("2026-11-02T15:10:00Z", Service.DMV, "Change an address", 3),
            asked("2026-11-02T15:30:00Z", Service.STUDENT_AID, "Repay a loan", 12),
            asked("2026-11-02T15:45:00Z", Service.SSA, "Replace a card", 6),
            asked("2026-11-02T19:00:00Z", Service.DMV, "Renew a license", 5),
            asked("2026-11-02T20:20:00Z", Service.DMV, "Change an address", 7));

    @Test
    @DisplayName("tst_xvy4kk Counts each service's questions, in the services' order")
    void byService() {
        var counts = Reports.byService(MONDAY);
        assertEquals(Map.of(Service.SSA, 2L, Service.STUDENT_AID, 1L, Service.DMV, 4L), counts);
        assertEquals(List.of(Service.SSA, Service.STUDENT_AID, Service.DMV), List.copyOf(counts.keySet()));
        assertEquals(Map.of(), Reports.byService(List.of()));
    }

    @Test
    @DisplayName("tst_mmkirg Gives the pages with the most questions, most first")
    void topPages() {
        assertEquals(
                List.of(new Reports.PageCount("Change an address", 2), new Reports.PageCount("Renew a license", 2)),
                Reports.topPages(MONDAY, 2));
        assertEquals(
                List.of(
                        new Reports.PageCount("Change an address", 2),
                        new Reports.PageCount("Renew a license", 2),
                        new Reports.PageCount("Replace a card", 2),
                        new Reports.PageCount("Repay a loan", 1)),
                Reports.topPages(MONDAY, 10));
    }

    @Test
    @DisplayName("tst_lut9eo Breaks a tie by the pages' names, with the most still first")
    void ties() {
        var log = new ArrayList<>(MONDAY);
        log.add(asked("2026-11-02T21:00:00Z", Service.STUDENT_AID, "Repay a loan", 2));
        log.add(asked("2026-11-02T21:10:00Z", Service.STUDENT_AID, "Repay a loan", 2));
        assertEquals(
                List.of(new Reports.PageCount("Repay a loan", 3), new Reports.PageCount("Change an address", 2)),
                Reports.topPages(log, 2));
    }

    @Test
    @DisplayName("tst_fzjt8z Gives no pages for 0, and refuses fewer")
    void noPages() {
        assertEquals(List.of(), Reports.topPages(MONDAY, 0));
        assertThrows(IllegalArgumentException.class, () -> Reports.topPages(MONDAY, -1));
    }

    @Test
    @DisplayName("tst_n319g5 Gives the median reply, the middle one's or the mean of two")
    void median() {
        assertEquals(Optional.of(Duration.ofSeconds(6)), Reports.medianReply(MONDAY));
        assertEquals(Optional.of(Duration.ofMillis(5500)), Reports.medianReply(MONDAY.subList(0, 6)));
        assertEquals(Optional.empty(), Reports.medianReply(List.of()));
    }

    @Test
    @DisplayName("tst_wj8la3 Leaves the log it's given as it was")
    void leavesTheLog() {
        var log = new ArrayList<>(MONDAY);
        Reports.medianReply(log);
        Reports.topPages(log, 3);
        assertEquals(MONDAY, log);
    }

    @Test
    @DisplayName("tst_lnunip Counts the questions in each hour, in order, on the zone's clock")
    void byHour() {
        var hours = Reports.byHour(MONDAY, NEW_YORK);
        assertInstanceOf(SortedMap.class, hours);
        assertEquals(Map.of(9, 2L, 10, 3L, 14, 1L, 15, 1L), hours);
        assertEquals(List.of(9, 10, 14, 15), List.copyOf(hours.keySet()));
        assertEquals(Map.of(14, 2L, 15, 3L, 19, 1L, 20, 1L), Reports.byHour(MONDAY, ZoneId.of("UTC")));
    }

    @Test
    @DisplayName("tst_xq0q91 Reads each question's hour with the offset of its own day")
    void clockChange() {
        // New York's clocks went back an hour on Sunday 1 November 2026.
        var log = List.of(
                asked("2026-10-30T13:30:00Z", Service.SSA, "Replace a card", 5),
                asked("2026-11-02T13:30:00Z", Service.SSA, "Replace a card", 5));
        assertEquals(Map.of(8, 1L, 9, 1L), Reports.byHour(log, NEW_YORK));
    }
}
