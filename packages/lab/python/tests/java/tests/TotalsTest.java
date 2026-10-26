import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class TotalsTest {
    @Test
    @DisplayName("tst_java01 Adds the amounts")
    void adds() {
        assertEquals(1255, Totals.sum(List.of(1250, 5)));
    }

    @Test
    @DisplayName("tst_java02 Shows dollars and cents")
    void dollars() {
        assertEquals("0.05", Totals.dollars(5));
    }

    @Test
    @DisplayName("tst_java03 Writes a total as JSON")
    void json() {
        assertEquals("{\"cents\":5}", Totals.json(5));
    }
}
