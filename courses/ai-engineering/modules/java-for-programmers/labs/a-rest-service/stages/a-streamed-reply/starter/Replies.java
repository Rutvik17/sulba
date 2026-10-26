import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;

/** The desk's replies: the caller's message in, and the agent's reply out as server-sent events,
 * each piece as it comes, through the gate in front of the model. */
public final class Replies implements HttpHandler {
    /** The caller's message. */
    public record Say(String content) {}

    public Replies(Agent agent, Gate gate) {}

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
