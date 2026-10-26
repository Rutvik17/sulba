import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** The desk's live counts of the questions it answers, which every request handler adds to at
 * once and the dashboard reads while they do. */
public final class Tally {
    private final LongAdder total = new LongAdder();
    private final ConcurrentHashMap<Service, LongAdder> services = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, LongAdder> pages = new ConcurrentHashMap<>();

    /** Counts a question, from any thread. */
    public void record(Reports.Asked asked) {
        services.computeIfAbsent(asked.service(), key -> new LongAdder()).increment();
        pages.computeIfAbsent(asked.page(), key -> new LongAdder()).increment();
        total.increment();
    }

    /** How many questions it has counted. */
    public long total() {
        return total.sum();
    }

    /** How many questions each service has had, in the order the services are declared, as they
     * stand now. */
    public Map<Service, Long> byService() {
        var counts = new EnumMap<Service, Long>(Service.class);
        services.forEach((service, count) -> counts.put(service, count.sum()));
        return Collections.unmodifiableMap(counts);
    }

    /** The n pages with the most questions now, most first, and pages with as many in the order of
     * their names. */
    public List<Reports.PageCount> topPages(int n) {
        return pages.entrySet().stream()
                .map(entry -> new Reports.PageCount(entry.getKey(), entry.getValue().sum()))
                .sorted(Comparator.comparingLong(Reports.PageCount::questions)
                        .reversed()
                        .thenComparing(Reports.PageCount::page))
                .limit(n)
                .toList();
    }
}
