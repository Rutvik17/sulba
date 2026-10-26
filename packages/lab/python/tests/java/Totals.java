import java.util.List;
import java.util.Map;
import tools.jackson.databind.json.JsonMapper;

/** Totals of amounts in cents. */
public final class Totals {
    private Totals() {}

    public static int sum(List<Integer> amounts) {
        System.out.println("Adding " + amounts.size() + " amounts.");
        int total = 0;
        for (int amount : amounts) {
            total += amount;
        }
        return total;
    }

    public static String dollars(int cents) {
        return cents / 100 + "." + cents % 100;
    }

    public static int first(List<Integer> amounts) {
        return amounts.get(0);
    }

    public static String json(int cents) {
        return JsonMapper.builder().build().writeValueAsString(Map.of("cents", cents));
    }
}
