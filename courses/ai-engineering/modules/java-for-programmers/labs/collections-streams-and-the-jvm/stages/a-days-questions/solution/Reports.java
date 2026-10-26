import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.SortedMap;
import java.util.TreeMap;
import java.util.stream.Collectors;

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
        return log.stream()
                .collect(Collectors.groupingBy(Asked::service, () -> new EnumMap<>(Service.class), Collectors.counting()));
    }

    /** The n pages with the most questions, most first, and pages with as many in the order of
     * their names. */
    public static List<PageCount> topPages(List<Asked> log, int n) {
        return log.stream()
                .collect(Collectors.groupingBy(Asked::page, Collectors.counting()))
                .entrySet()
                .stream()
                .map(entry -> new PageCount(entry.getKey(), entry.getValue()))
                .sorted(Comparator.comparingLong(PageCount::questions).reversed().thenComparing(PageCount::page))
                .limit(n)
                .toList();
    }

    /** How long the median reply took: the middle reply's time, or the mean of the middle two,
     * and none for an empty log. */
    public static Optional<Duration> medianReply(List<Asked> log) {
        var replies = log.stream().map(Asked::reply).sorted().toList();
        if (replies.isEmpty()) {
            return Optional.empty();
        }
        var middle = replies.size() / 2;
        return Optional.of(
                replies.size() % 2 == 1
                        ? replies.get(middle)
                        : replies.get(middle - 1).plus(replies.get(middle)).dividedBy(2));
    }

    /** How many questions were asked in each hour of the day, from 0 to 23, on the clock of the
     * zone, in order, leaving out an hour with none. */
    public static SortedMap<Integer, Long> byHour(List<Asked> log, ZoneId zone) {
        return log.stream()
                .collect(Collectors.groupingBy(
                        asked -> asked.at().atZone(zone).getHour(), TreeMap::new, Collectors.counting()));
    }
}
