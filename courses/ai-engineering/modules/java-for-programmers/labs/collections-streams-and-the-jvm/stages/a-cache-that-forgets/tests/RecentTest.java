import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class RecentTest {
    static Recent<String, String> three() {
        var recent = new Recent<String, String>(3);
        recent.put("a", "Ann's conversation");
        recent.put("b", "Bo's conversation");
        recent.put("c", "Cy's conversation");
        return recent;
    }

    @Test
    @DisplayName("tst_1xxv70 Holds values by their keys")
    void holds() {
        var recent = three();
        assertEquals(Optional.of("Bo's conversation"), recent.get("b"));
        assertEquals(Optional.empty(), recent.get("z"));
        assertEquals(3, recent.size());
    }

    @Test
    @DisplayName("tst_5v5y8h Forgets the one used least lately to make room")
    void forgets() {
        var recent = three();
        recent.put("d", "Di's conversation");
        assertEquals(List.of("b", "c", "d"), recent.keys());
        assertEquals(Optional.empty(), recent.get("a"));
        assertEquals(3, recent.size());
    }

    @Test
    @DisplayName("tst_oqbg7e Counts a get as a use")
    void getsAreUses() {
        var recent = three();
        recent.get("a");
        assertEquals(List.of("b", "c", "a"), recent.keys());
        recent.put("d", "Di's conversation");
        assertEquals(List.of("c", "a", "d"), recent.keys());
        assertEquals(Optional.of("Ann's conversation"), recent.get("a"));
    }

    @Test
    @DisplayName("tst_5ietlv Replaces a key's value as a use, without growing")
    void replaces() {
        var recent = three();
        recent.put("a", "Ann's new conversation");
        assertEquals(List.of("b", "c", "a"), recent.keys());
        assertEquals(Optional.of("Ann's new conversation"), recent.get("a"));
        assertEquals(3, recent.size());
    }

    @Test
    @DisplayName("tst_7cfjx0 Leaves the order alone for a key it doesn't hold, and forgets on remove")
    void misses() {
        var recent = three();
        recent.get("z");
        assertEquals(List.of("a", "b", "c"), recent.keys());
        assertEquals(Optional.of("Bo's conversation"), recent.remove("b"));
        assertEquals(Optional.empty(), recent.remove("b"));
        assertEquals(List.of("a", "c"), recent.keys());
    }

    @Test
    @DisplayName("tst_1hqama Gives its keys as a copy")
    void keysAreACopy() {
        var recent = three();
        assertThrows(UnsupportedOperationException.class, () -> recent.keys().clear());
        var keys = recent.keys();
        recent.put("d", "Di's conversation");
        assertEquals(List.of("a", "b", "c"), keys);
    }

    @Test
    @DisplayName("tst_nsvslf Refuses a cache of no values, and a key or value that's null")
    void refuses() {
        assertThrows(IllegalArgumentException.class, () -> new Recent<String, String>(0));
        var recent = three();
        assertThrows(NullPointerException.class, () -> recent.put(null, "Nobody's"));
        assertThrows(NullPointerException.class, () -> recent.put("n", null));
        assertThrows(NullPointerException.class, () -> recent.get(null));
        assertEquals(List.of("a", "b", "c"), recent.keys());
    }

    @Test
    @DisplayName("tst_l26wdp Holds one value with room for one, of any types")
    void anyTypes() {
        var recent = new Recent<UUID, List<String>>(1);
        var first = UUID.fromString("00000000-0000-4000-8000-000000000001");
        var second = UUID.fromString("00000000-0000-4000-8000-000000000002");
        recent.put(first, List.of("Hello."));
        recent.put(second, List.of("Hi.", "Is my card on its way?"));
        assertEquals(List.of(second), recent.keys());
        assertEquals(Optional.of(List.of("Hi.", "Is my card on its way?")), recent.get(second));
    }
}
