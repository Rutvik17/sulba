import java.util.List;

/** An invoice for a customer: its amounts, in cents. */
public record Invoice(String customer, List<Integer> cents) {
    public Invoice {
        if (customer == null || customer.isBlank()) {
            throw new IllegalArgumentException("An invoice needs a customer.");
        }
        cents = List.copyOf(cents);
    }

    /** The sum of the invoice's amounts. */
    public int total() {
        return cents.stream().mapToInt(Integer::intValue).sum();
    }
}
