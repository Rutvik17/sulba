import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.time.LocalDate;
import java.time.LocalTime;
import tools.jackson.databind.json.JsonMapper;

/** The desk's API: the caller's tickets and the callbacks booked on them, as JSON, with every
 * error as problem details. */
public final class Api implements HttpHandler {
    /** What opening a ticket takes. */
    public record NewTicket(Service service, String summary) {}

    /** What booking a callback takes. */
    public record NewCallback(LocalDate day, LocalTime time) {}

    /** How the API reads and writes JSON. */
    public static final JsonMapper JSON = JsonMapper.builder().build();

    public Api(Desk desk) {}

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
