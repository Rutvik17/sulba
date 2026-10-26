import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/** Problem details (RFC 9457) for every error the desk's API answers with. */
public final class Problems {
    /** The media type of a problem details object as JSON. */
    public static final String MEDIA_TYPE = "application/problem+json";

    /** A value in a request that doesn't fit: what's wrong, and where it is, as a JSON Pointer in
     * a URI fragment. */
    public record Invalid(String detail, String pointer) {}

    /** A problem details object, without its detail or errors when it has none. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record Problem(String type, String title, int status, String detail, List<Invalid> errors) {}

    private Problems() {}

    /** A problem for the status: of type about:blank, titled with the status's phrase, and with
     * the detail, if there is one. */
    public static Problem of(int status, String detail) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The problem the desk's API answers with for an error, from the first in it or its causes
     * that the API knows. */
    public static Problem of(Throwable error) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Where a value is in a request's JSON, from the keys and indexes that lead to it: a JSON
     * Pointer in a URI fragment. */
    public static String pointer(List<?> path) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The problem as JSON. */
    public static String json(Problem problem) {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
