import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class TallyTest {
    static Reports.Asked asked(Service service, String page) {
        return new Reports.Asked(Instant.parse("2026-11-02T14:05:00Z"), service, page, Duration.ofSeconds(4));
    }

    static Tally monday() {
        var tally = new Tally();
        tally.record(asked(Service.DMV, "Renew a license"));
        tally.record(asked(Service.SSA, "Replace a card"));
        tally.record(asked(Service.DMV, "Change an address"));
        tally.record(asked(Service.SSA, "Replace a card"));
        tally.record(asked(Service.DMV, "Renew a license"));
        return tally;
    }

    @Test
    @DisplayName("tst_onhk36 Counts the questions it's given")
    void counts() {
        assertEquals(5, monday().total());
        assertEquals(0, new Tally().total());
    }

    @Test
    @DisplayName("tst_kqn5td Counts each service's questions, in the services' order")
    void byService() {
        var counts = monday().byService();
        assertEquals(Map.of(Service.SSA, 2L, Service.DMV, 3L), counts);
        assertEquals(List.of(Service.SSA, Service.DMV), List.copyOf(counts.keySet()));
    }

    @Test
    @DisplayName("tst_jg7wuj Gives the pages with the most questions, ties by name")
    void topPages() {
        assertEquals(
                List.of(new Reports.PageCount("Renew a license", 2), new Reports.PageCount("Replace a card", 2)),
                monday().topPages(2));
        assertEquals(List.of(), new Tally().topPages(3));
    }

    @Test
    @DisplayName("tst_1x43ei Counts from a few threads at once")
    void fewThreads() throws Exception {
        var tally = new Tally();
        try (var threads = Executors.newFixedThreadPool(4)) {
            for (var thread = 0; thread < 4; thread++) {
                threads.submit(() -> {
                    for (var question = 0; question < 1000; question++) {
                        tally.record(asked(Service.VA, "Apply for a pension"));
                    }
                });
            }
        }
        assertEquals(4000, tally.total());
        assertEquals(List.of(new Reports.PageCount("Apply for a pension", 4000)), tally.topPages(1));
    }
}
