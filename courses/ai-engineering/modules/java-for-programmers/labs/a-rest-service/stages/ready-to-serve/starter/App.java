import java.io.IOException;
import java.net.InetSocketAddress;
import java.time.Duration;
import java.util.Map;
import java.util.function.Consumer;

/** The desk's service, ready to serve: its settings from the environment, and a stop that lets
 * the replies in flight finish. */
public final class App {
    /** Where the service listens, its gate's places, line and limit, and how many seconds a stop
     * waits for the requests in flight. */
    public record Settings(String host, int port, int running, int waiting, Duration limit, int grace) {}

    /** Each setting's variable, with its value when the variable isn't set. */
    public static final Map<String, String> VARIABLES = Map.of(
            "DESK_HOST", "127.0.0.1",
            "DESK_PORT", "8080",
            "DESK_RUNNING", "2",
            "DESK_WAITING", "8",
            "DESK_SECONDS", "120",
            "DESK_GRACE", "10");

    /** The settings from the environment's variables, or an IllegalArgumentException that names
     * each variable that doesn't fit. */
    public static Settings settings(Map<String, String> environment) {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Starts the desk's service with the settings. */
    public static App start(Settings settings, Desk desk, Agent agent, Consumer<String> log) throws IOException {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** The address the service listens at. */
    public InetSocketAddress address() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Stops taking requests, gives those in flight up to the grace to finish, then interrupts
     * the rest, and returns once every one has ended. */
    public void stop() throws InterruptedException {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
