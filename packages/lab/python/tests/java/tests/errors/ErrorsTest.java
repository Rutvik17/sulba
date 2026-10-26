import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class ErrorsTest {
    @Test
    @DisplayName("tst_java04 Takes the first of no amounts")
    void first() {
        assertEquals(0, Totals.first(List.of()));
    }

    @Test
    @DisplayName("tst_java05 Takes the first of two")
    void firstOfTwo() {
        assertEquals(1250, Totals.first(List.of(1250, 5)));
    }
}
