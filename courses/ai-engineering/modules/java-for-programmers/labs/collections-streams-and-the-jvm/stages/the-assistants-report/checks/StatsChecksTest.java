import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class StatsChecksTest {
    static Reports.Asked asked(String at, Service service, String page, long seconds) {
        return new Reports.Asked(Instant.parse(at), service, page, Duration.ofSeconds(seconds));
    }

    @Test
    @DisplayName("tst_zblmks The questions from before forgotten, wherever they are")
    void prunes() {
        var stats = new Stats();
        stats.add(asked("2026-11-01T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T14:40:00Z", Service.SSA, "Replace a card", 9));
        stats.add(asked("2026-11-01T15:10:00Z", Service.DMV, "Change an address", 3));
        stats.add(asked("2026-11-01T16:00:00Z", Service.VA, "Apply for a pension", 8));
        stats.prune(Instant.parse("2026-11-02T00:00:00Z"));
        assertEquals(Map.of("Replace a card", Duration.ofSeconds(9)), stats.slowest());
    }

    @Test
    @DisplayName("tst_xi69er A page asked about twice")
    void slowest() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T15:10:00Z", Service.DMV, "Renew a license", 11));
        stats.add(asked("2026-11-02T16:30:00Z", Service.DMV, "Renew a license", 7));
        assertEquals(Map.of("Renew a license", Duration.ofSeconds(11)), stats.slowest());
    }

    @Test
    @DisplayName("tst_o3pj21 A busy day's busiest pages")
    void busiest() {
        var stats = new Stats();
        var start = Instant.parse("2026-11-02T14:00:00Z");
        for (var question = 0; question < 200; question++) {
            var at = start.plusSeconds(60L * question).toString();
            stats.add(asked(at, Service.DMV, "Renew a license", 4));
            stats.add(asked(at, Service.SSA, "Replace a card", 6));
        }
        stats.add(asked("2026-11-02T20:00:00Z", Service.VA, "Apply for a pension", 8));
        assertEquals(List.of("Renew a license", "Replace a card"), stats.busiest());
    }

    @Test
    @DisplayName("tst_s5bxls Questions in more than one hour")
    void byHourAndService() {
        var stats = new Stats();
        stats.add(asked("2026-11-02T14:05:00Z", Service.DMV, "Renew a license", 4));
        stats.add(asked("2026-11-02T15:10:00Z", Service.SSA, "Replace a card", 9));
        stats.add(asked("2026-11-02T15:20:00Z", Service.SSA, "Replace a card", 5));
        assertEquals(
                Map.of(List.of(9, Service.DMV), 1, List.of(10, Service.SSA), 2),
                stats.byHourAndService(ZoneId.of("America/New_York")));
    }
}
