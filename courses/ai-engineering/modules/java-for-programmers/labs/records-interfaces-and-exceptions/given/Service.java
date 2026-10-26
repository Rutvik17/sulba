import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Arrays;
import java.util.Optional;

/** The four services whose advisers the desk books, each with the id JSON gives it. */
public enum Service {
    SSA("ssa", "Social Security"),
    VA("va", "veterans' benefits"),
    STUDENT_AID("studentaid", "federal student aid"),
    DMV("dmv", "New York State's DMV");

    private final String id;
    private final String title;

    Service(String id, String title) {
        this.id = id;
        this.title = title;
    }

    /** The service's id, as JSON writes it, such as {@code ssa}. */
    @JsonValue
    public String id() {
        return id;
    }

    /** The service's name in a sentence, such as {@code Social Security}. */
    public String title() {
        return title;
    }

    /** The service with the id, or none. */
    public static Optional<Service> withId(String id) {
        return Arrays.stream(values()).filter(service -> service.id.equals(id)).findFirst();
    }
}
