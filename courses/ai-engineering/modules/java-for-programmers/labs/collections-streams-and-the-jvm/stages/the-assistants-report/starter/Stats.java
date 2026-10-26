import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/** The day's figures for the office's dashboard, from the questions the desk answered. */
public final class Stats {
    private final List<Reports.Asked> log = new ArrayList<>();

    /** Adds a question the desk answered. */
    public void add(Reports.Asked asked) {
        log.add(asked);
    }

    /** Forgets the questions asked before the instant, which the dashboard no longer shows. */
    public void prune(Instant before) {
        for (var asked : log) {
            if (asked.at().isBefore(before)) {
                log.remove(asked);
            }
        }
    }

    /** How many questions it holds. */
    public int size() {
        return log.size();
    }

    /** Each page's slowest reply. */
    public Map<String, Duration> slowest() {
        return log.stream().collect(Collectors.toMap(Reports.Asked::page, Reports.Asked::reply));
    }

    /** The pages with the most questions, in the order of their names. */
    public List<String> busiest() {
        var counts = new HashMap<String, Integer>();
        for (var asked : log) {
            counts.merge(asked.page(), 1, Integer::sum);
        }
        if (counts.isEmpty()) {
            return List.of();
        }
        Integer most = Collections.max(counts.values());
        return counts.entrySet().stream()
                .filter(entry -> entry.getValue() == most)
                .map(Map.Entry::getKey)
                .sorted()
                .toList();
    }

    /** How many questions each service had in each hour of the day on the zone's clock, by the
     * hour and the service. */
    public Map<List<Object>, Integer> byHourAndService(ZoneId zone) {
        var counts = new HashMap<List<Object>, Integer>();
        var key = new ArrayList<Object>();
        for (var asked : log) {
            key.clear();
            key.add(asked.at().atZone(zone).getHour());
            key.add(asked.service());
            counts.merge(key, 1, Integer::sum);
        }
        return counts;
    }
}
