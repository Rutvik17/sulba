import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.SortedMap;

/** Reports from the desk's log of the questions it answered. */
public final class Reports {
    /** One question the desk answered: when it was asked, the service it was about, the help page
     * it was asked from, and how long the reply took. */
    public record Asked(Instant at, Service service, String page, Duration reply) {}

    /** A help page, and how many questions were asked from it. */
    public record PageCount(String page, long questions) {}

    private Reports() {}

    /** How many questions each service had, in the order the services are declared, leaving out
     * a service with none. */
    public static Map<Service, Long> byService(List<Asked> log) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The n pages with the most questions, most first, and pages with as many in the order of
     * their names. */
    public static List<PageCount> topPages(List<Asked> log, int n) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** How long the median reply took: the middle reply's time, or the mean of the middle two,
     * and none for an empty log. */
    public static Optional<Duration> medianReply(List<Asked> log) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** How many questions were asked in each hour of the day, from 0 to 23, on the clock of the
     * zone, in order, leaving out an hour with none. */
    public static SortedMap<Integer, Long> byHour(List<Asked> log, ZoneId zone) {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
