import java.util.List;
import java.util.Map;
import java.util.SortedSet;

/** The help pages' passages indexed by their words, and a search that ranks passages by how many
 * of a query's words they have. */
public final class Index {
    /** A passage the search found, and how many of the query's words it has. */
    public record Hit(String passage, int shared) {}

    /** Indexes each passage's text, by the passage's id. */
    public Index(Map<String, String> texts) {}

    /** A text's words: its runs of letters, digits and underscores, lowercased, in order. */
    public static List<String> words(String text) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The ids of the passages that have the word, in order. */
    public SortedSet<String> passagesWith(String word) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The k passages that have the most of the query's words, each word counted once, most
     * first, and passages with as many in the order of their ids. A passage with none of them
     * isn't found. */
    public List<Hit> find(String query, int k) {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
