import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;
import java.util.regex.Pattern;

/** The help pages' passages indexed by their words, and a search that ranks passages by how many
 * of a query's words they have. */
public final class Index {
    /** A passage the search found, and how many of the query's words it has. */
    public record Hit(String passage, int shared) {}

    private static final Pattern WORD = Pattern.compile("\\w+", Pattern.UNICODE_CHARACTER_CLASS);

    private final Map<String, SortedSet<String>> passages = new HashMap<>();

    /** Indexes each passage's text, by the passage's id. */
    public Index(Map<String, String> texts) {
        texts.forEach((id, text) -> {
            for (var word : words(text)) {
                passages.computeIfAbsent(word, key -> new TreeSet<>()).add(id);
            }
        });
    }

    /** A text's words: its runs of letters, digits and underscores, lowercased, in order. */
    public static List<String> words(String text) {
        return WORD.matcher(text.toLowerCase(Locale.ROOT)).results().map(match -> match.group()).toList();
    }

    /** The ids of the passages that have the word, in order. */
    public SortedSet<String> passagesWith(String word) {
        return Collections.unmodifiableSortedSet(passages.getOrDefault(word, new TreeSet<>()));
    }

    /** The k passages that have the most of the query's words, each word counted once, most
     * first, and passages with as many in the order of their ids. A passage with none of them
     * isn't found. */
    public List<Hit> find(String query, int k) {
        var shared = new HashMap<String, Integer>();
        for (var word : new LinkedHashSet<>(words(query))) {
            for (var id : passagesWith(word)) {
                shared.merge(id, 1, Integer::sum);
            }
        }
        return shared.entrySet().stream()
                .map(entry -> new Hit(entry.getKey(), entry.getValue()))
                .sorted(Comparator.comparingInt(Hit::shared).reversed().thenComparing(Hit::passage))
                .limit(k)
                .toList();
    }
}
