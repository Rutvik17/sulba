import java.util.List;
import java.util.Optional;

/** The values used most lately, by their keys, up to a number of them: putting one more forgets
 * the one used least lately. */
public final class Recent<K, V> {
    public Recent(int capacity) {}

    /** The key's value, if the cache holds it, which counts as using it. */
    public Optional<V> get(K key) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Holds the value by its key, in place of any it held before, which counts as using it. */
    public void put(K key, V value) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Forgets the key's value, and gives it, if the cache held it. */
    public Optional<V> remove(K key) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The keys the cache holds, the one used least lately first. */
    public List<K> keys() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** How many values the cache holds. */
    public int size() {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
