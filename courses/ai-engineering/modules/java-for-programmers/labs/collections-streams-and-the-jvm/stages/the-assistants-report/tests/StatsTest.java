import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class StatsTest {
    static Reports.Asked asked(String at, Service service, String page, long seconds) {
        return new Reports.Asked(Instant.parse(at), service, page, Duration.ofSeconds(seconds));
    }

    @Test
    @DisplayName("tst_d9wgck Holds the questions added")
    void adds() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9));
        assertEquals(2, stats.size());
    }

    @Test
    @DisplayName("tst_egy4qq Forgets the questions from before")
    void prunes() {
        var stats = new Stats();
        stats.add(asked("2026-11-01T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9));
        stats.prune(Instant.parse("2026-11-02T00:00:00Z"));
        assertEquals(1, stats.size());
        assertEquals(Map.of("Replace a card", Duration.ofSeconds(9)), stats.slowest());
    }

    @Test
    @DisplayName("tst_be43ka Gives each page's slowest reply")
    void slowest() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9));
        assertEquals(
                Map.of("Renew a license", Duration.ofSeconds(4), "Replace a card", Duration.ofSeconds(9)),
                stats.slowest());
    }

    @Test
    @DisplayName("tst_e3l13c Gives the pages with the most questions")
    void busiest() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9));
        stats.add(asked("2026-11-02T15:10:00Z", Service.DMV, "Renew a license", 3));
        stats.add(asked("2026-11-02T15:45:00Z", Service.SSA, "Replace a card", 6));
        stats.add(asked("2026-11-02T16:00:00Z", Service.VA, "Apply for a pension", 8));
        assertEquals(List.of("Renew a license", "Replace a card"), stats.busiest());
        assertEquals(List.of(), new Stats().busiest());
    }

    @Test
    @DisplayName("tst_5jmsca Counts each service's questions by the hour")
    void byHourAndService() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:50:00Z", Service.DMV, "Change an address", 3));
        assertEquals(Map.of(List.of(9, Service.DMV), 2), stats.byHourAndService(ZoneId.of("America/New_York")));
    }
}
