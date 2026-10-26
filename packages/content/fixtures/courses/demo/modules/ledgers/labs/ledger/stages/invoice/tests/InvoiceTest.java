import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class InvoiceTest {
    @Test
    @DisplayName("tst_demo32 Adds up its amounts")
    void total() {
        assertEquals(1255, new Invoice("Kim", List.of(1250, 5)).total());
    }

    @Test
    @DisplayName("tst_demo33 Refuses a blank customer, and keeps its own amounts")
    void checks() {
        assertThrows(IllegalArgumentException.class, () -> new Invoice(" ", List.of()));
        var amounts = new ArrayList<>(List.of(1250));
        var invoice = new Invoice("Kim", amounts);
        amounts.add(5);
        assertEquals(1250, invoice.total());
    }
}
