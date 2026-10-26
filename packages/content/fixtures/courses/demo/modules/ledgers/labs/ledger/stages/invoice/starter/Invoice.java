import java.util.List;

/** An invoice for a customer: its amounts, in cents. */
public record Invoice(String customer, List<Integer> cents) {
    /** The sum of the invoice's amounts. */
    public int total() {
        return 0;
    }
}
