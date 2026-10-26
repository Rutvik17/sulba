import java.util.List;
import java.util.Map;

/** The desk's live counts of the questions it answers, which every request handler adds to at
 * once and the dashboard reads while they do. */
public final class Tally {
    /** Counts a question, from any thread. */
    public void record(Reports.Asked asked) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** How many questions it has counted. */
    public long total() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** How many questions each service has had, in the order the services are declared, as they
     * stand now. */
    public Map<Service, Long> byService() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The n pages with the most questions now, most first, and pages with as many in the order of
     * their names. */
    public List<Reports.PageCount> topPages(int n) {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
