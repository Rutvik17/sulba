import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class TallyChecksTest {
    static final Service[] SERVICES = Service.values();

    static Reports.Asked asked(Service service, String page) {
        return new Reports.Asked(Instant.parse("2026-11-02T14:05:00Z"), service, page, Duration.ofSeconds(4));
    }

    @Test
    @DisplayName("tst_b31dzk Every count right with ten thousand threads at once")
    void contention() {
        var tally = new Tally();
        try (var threads = Executors.newVirtualThreadPerTaskExecutor()) {
            for (var thread = 0; thread < 10_000; thread++) {
                var service = SERVICES[thread % SERVICES.length];
                threads.submit(() -> {
                    for (var question = 0; question < 100; question++) {
                        tally.record(asked(service, "Page " + question % 20));
                    }
                });
            }
        }
        assertEquals(1_000_000, tally.total());
        assertEquals(
                Map.of(Service.SSA, 250_000L, Service.VA, 250_000L, Service.STUDENT_AID, 250_000L, Service.DMV, 250_000L),
                tally.byService());
        var pages = tally.topPages(25);
        assertEquals(20, pages.size());
        for (var page : pages) {
            assertEquals(50_000, page.questions(), page.page());
        }
    }

    @Test
    @DisplayName("tst_dv87cw A new page's first questions, counted all at once")
    void firstQuestions() throws Exception {
        for (var round = 0; round < 200; round++) {
            var tally = new Tally();
            var start = new CountDownLatch(1);
            try (var threads = Executors.newVirtualThreadPerTaskExecutor()) {
                for (var thread = 0; thread < 64; thread++) {
                    threads.submit(() -> {
                        start.await();
                        tally.record(asked(Service.SSA, "Replace a card"));
                        return null;
                    });
                }
                start.countDown();
            }
            assertEquals(List.of(new Reports.PageCount("Replace a card", 64)), tally.topPages(1), "round " + round);
            assertEquals(Map.of(Service.SSA, 64L), tally.byService(), "round " + round);
        }
    }

    @Test
    @DisplayName("tst_7wk86f Read while it counts")
    void readWhileCounting() {
        var tally = new Tally();
        var totals = new ArrayList<Long>();
        try (var threads = Executors.newVirtualThreadPerTaskExecutor()) {
            var writers = new ArrayList<Future<?>>();
            for (var thread = 0; thread < 8; thread++) {
                var service = SERVICES[thread % SERVICES.length];
                writers.add(threads.submit(() -> {
                    for (var question = 0; question < 50_000; question++) {
                        tally.record(asked(service, "Page " + question % 500));
                    }
                }));
            }
            // The dashboard reads on this thread until every writer is done.
            while (!writers.stream().allMatch(Future::isDone)) {
                tally.topPages(10);
                tally.byService();
                totals.add(tally.total());
            }
        }
        for (var index = 1; index < totals.size(); index++) {
            assertTrue(totals.get(index) >= totals.get(index - 1), "the total went down");
        }
        assertEquals(400_000, tally.total());
    }

    @Test
    @DisplayName("tst_an31mq A report stays as it was given")
    void reportsStay() {
        var tally = new Tally();
        tally.record(asked(Service.DMV, "Renew a license"));
        var services = tally.byService();
        var pages = tally.topPages(5);
        tally.record(asked(Service.DMV, "Renew a license"));
        tally.record(asked(Service.SSA, "Replace a card"));
        assertEquals(Map.of(Service.DMV, 1L), services);
        assertEquals(List.of(new Reports.PageCount("Renew a license", 1)), pages);
        assertThrows(UnsupportedOperationException.class, () -> services.put(Service.VA, 9L));
        assertThrows(UnsupportedOperationException.class, () -> pages.clear());
    }
}
