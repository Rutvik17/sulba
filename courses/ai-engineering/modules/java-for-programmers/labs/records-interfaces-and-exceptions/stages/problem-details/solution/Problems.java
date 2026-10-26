import com.fasterxml.jackson.annotation.JsonInclude;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import tools.jackson.core.JacksonException;
import tools.jackson.core.exc.StreamReadException;
import tools.jackson.databind.DatabindException;
import tools.jackson.databind.exc.InvalidDefinitionException;
import tools.jackson.databind.exc.UnrecognizedPropertyException;
import tools.jackson.databind.exc.ValueInstantiationException;
import tools.jackson.databind.json.JsonMapper;

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

    private static final Map<Integer, String> TITLES = Map.of(
            400, "Bad Request",
            404, "Not Found",
            405, "Method Not Allowed",
            409, "Conflict",
            413, "Content Too Large",
            415, "Unsupported Media Type",
            422, "Unprocessable Content",
            429, "Too Many Requests",
            500, "Internal Server Error",
            503, "Service Unavailable");

    // The characters a URI fragment holds as they are, besides letters and digits.
    private static final String FRAGMENT = "-._~!$&'()*+,;=:@/?";

    private static final JsonMapper JSON = JsonMapper.builder().build();

    private Problems() {}

    /** A problem for the status: of type about:blank, titled with the status's phrase, and with
     * the detail, if there is one. */
    public static Problem of(int status, String detail) {
        return of(status, detail, null);
    }

    /** The problem the desk's API answers with for an error, from the first in it or its causes
     * that the API knows. */
    public static Problem of(Throwable error) {
        var seen = new HashSet<Throwable>();
        for (var each = error; each != null && seen.add(each); each = each.getCause()) {
            switch (each) {
                case Desk.Refused refused -> {
                    return of(409, refused.getMessage());
                }
                case InvalidDefinitionException definition -> {
                    return of(500, null);
                }
                case DatabindException unfit -> {
                    var at = pointer(unfit.getPath().stream()
                            .<Object>map(reference -> reference.getPropertyName() != null
                                    ? reference.getPropertyName()
                                    : reference.getIndex())
                            .toList());
                    return of(422, "The request's content doesn't fit.", List.of(new Invalid(why(unfit), at)));
                }
                case StreamReadException unread -> {
                    return of(400, "The request's body isn't JSON.");
                }
                default -> {}
            }
        }
        return of(500, null);
    }

    /** Where a value is in a request's JSON, from the keys and indexes that lead to it: a JSON
     * Pointer in a URI fragment. */
    public static String pointer(List<?> path) {
        var pointer = new StringBuilder("#");
        for (var part : path) {
            var escaped = part.toString().replace("~", "~0").replace("/", "~1");
            pointer.append('/');
            for (var octet : escaped.getBytes(StandardCharsets.UTF_8)) {
                var c = (char) (octet & 0xff);
                if (c < 0x80 && (Character.isLetterOrDigit(c) || FRAGMENT.indexOf(c) >= 0)) {
                    pointer.append(c);
                } else {
                    pointer.append('%').append(String.format("%02X", octet & 0xff));
                }
            }
        }
        return pointer.toString();
    }

    /** The problem as JSON. */
    public static String json(Problem problem) {
        return JSON.writeValueAsString(problem);
    }

    private static Problem of(int status, String detail, List<Invalid> errors) {
        var title = TITLES.get(status);
        if (title == null) {
            throw new IllegalArgumentException("The desk gives no problem with the status " + status + ".");
        }
        return new Problem("about:blank", title, status, detail, errors);
    }

    private static String why(JacksonException unfit) {
        return switch (unfit) {
            case ValueInstantiationException refused when refused.getCause() != null ->
                refused.getCause().getMessage();
            case UnrecognizedPropertyException unknown -> "There's no such field.";
            default -> "The value doesn't fit this field.";
        };
    }
}
