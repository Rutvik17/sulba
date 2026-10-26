import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class IndexTest {
    /** Passages from the four services' help pages, written for the lab. */
    static final Map<String, String> PASSAGES = Map.of(
            "p1", "To replace a lost Social Security card, apply online or call us.",
            "p2", "Your new card arrives in about two weeks. A lost card can't be used again.",
            "p3", "Change the address on your license online, within 10 days of moving.",
            "p4", "Renew your license online up to a year before it expires.",
            "p5", "Student loan payments restart in the month after your grace period ends.",
            "p6", "Veterans can apply online for a pension, or call a VA office.");

    static final Index INDEX = new Index(PASSAGES);

    @Test
    @DisplayName("tst_z61xhh Splits a text into its words, lowercased")
    void words() {
        assertEquals(List.of("replace", "a", "lost", "card"), Index.words("Replace a LOST card."));
        assertEquals(List.of("can", "t", "be", "used", "form_1040", "2026"), Index.words("Can't be used: form_1040, 2026!"));
        assertEquals(List.of(), Index.words(" ... "));
    }

    @Test
    @DisplayName("tst_z6xsib Keeps letters outside ASCII in their words")
    void unicode() {
        assertEquals(List.of("café", "naïve", "über", "ñandú"), Index.words("Café, naïve: ÜBER Ñandú"));
    }

    @Test
    @DisplayName("tst_bbdcsd Lowercases the same way on a computer set to any language")
    void anyLocale() {
        var before = Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"));
            assertEquals(List.of("title", "id"), Index.words("TITLE ID"));
        } finally {
            Locale.setDefault(before);
        }
    }

    @Test
    @DisplayName("tst_qo1vyh Gives the passages with a word, in order")
    void passagesWith() {
        assertEquals(List.of("p1", "p3", "p4", "p6"), List.copyOf(INDEX.passagesWith("online")));
        assertEquals(List.of("p1", "p2"), List.copyOf(INDEX.passagesWith("lost")));
        assertEquals(Set.of(), INDEX.passagesWith("passport"));
    }

    @Test
    @DisplayName("tst_d5eydl Gives sets that can't change the index")
    void readOnly() {
        assertThrows(UnsupportedOperationException.class, () -> INDEX.passagesWith("card").clear());
        assertThrows(UnsupportedOperationException.class, () -> INDEX.passagesWith("passport").add("p9"));
        assertEquals(List.of("p1", "p2"), List.copyOf(INDEX.passagesWith("card")));
        assertEquals(Set.of(), INDEX.passagesWith("passport"));
    }

    @Test
    @DisplayName("tst_m0lkpg Ranks passages by how many of the query's words they have")
    void find() {
        assertEquals(
                List.of(new Index.Hit("p1", 4), new Index.Hit("p2", 2), new Index.Hit("p3", 1)),
                INDEX.find("Replace my lost card, or change it", 3));
    }

    @Test
    @DisplayName("tst_c74u89 Counts a word the query repeats once")
    void repeats() {
        assertEquals(List.of(new Index.Hit("p1", 2), new Index.Hit("p2", 2)), INDEX.find("card CARD card lost", 5));
    }

    @Test
    @DisplayName("tst_l4cn6d Breaks ties by id, and finds no passage that shares no word")
    void ties() {
        assertEquals(
                List.of(new Index.Hit("p1", 1), new Index.Hit("p3", 1), new Index.Hit("p4", 1), new Index.Hit("p6", 1)),
                INDEX.find("online", 10));
        assertEquals(List.of(new Index.Hit("p1", 1)), INDEX.find("online", 1));
        assertEquals(List.of(), INDEX.find("passport", 3));
        assertEquals(List.of(), INDEX.find("online", 0));
    }
}
