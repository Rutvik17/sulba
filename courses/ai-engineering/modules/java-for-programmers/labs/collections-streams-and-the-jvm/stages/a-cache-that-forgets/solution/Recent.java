import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/** The values used most lately, by their keys, up to a number of them: putting one more forgets
 * the one used least lately. */
public final class Recent<K, V> {
    private final int capacity;
    private final LinkedHashMap<K, V> held;

    public Recent(int capacity) {
        if (capacity < 1) {
            throw new IllegalArgumentException("A cache holds at least 1 value, not " + capacity + ".");
        }
        this.capacity = capacity;
        // In access order, so each get or put moves its entry to the end.
        this.held = new LinkedHashMap<>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
                return size() > Recent.this.capacity;
            }
        };
    }

    /** The key's value, if the cache holds it, which counts as using it. */
    public Optional<V> get(K key) {
        return Optional.ofNullable(held.get(Objects.requireNonNull(key, "key")));
    }

    /** Holds the value by its key, in place of any it held before, which counts as using it. */
    public void put(K key, V value) {
        held.put(Objects.requireNonNull(key, "key"), Objects.requireNonNull(value, "value"));
    }

    /** Forgets the key's value, and gives it, if the cache held it. */
    public Optional<V> remove(K key) {
        return Optional.ofNullable(held.remove(Objects.requireNonNull(key, "key")));
    }

    /** The keys the cache holds, the one used least lately first. */
    public List<K> keys() {
        return List.copyOf(held.keySet());
    }

    /** How many values the cache holds. */
    public int size() {
        return held.size();
    }
}
