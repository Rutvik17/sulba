import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
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

    private final HttpServer server;
    private final int grace;

    private App(HttpServer server, int grace) {
        this.server = server;
        this.grace = grace;
    }

    /** The settings from the environment's variables, or an IllegalArgumentException that names
     * each variable that doesn't fit. */
    public static Settings settings(Map<String, String> environment) {
        var wrong = new ArrayList<String>();
        var host = value(environment, "DESK_HOST");
        if (host.isBlank()) {
            wrong.add("DESK_HOST is a host name or an address, not \"" + host + "\".");
        }
        var port = number(environment, "DESK_PORT", 0, 65535, "a port from 0 to 65535", wrong);
        var running = number(environment, "DESK_RUNNING", 1, Integer.MAX_VALUE, "a whole number from 1", wrong);
        var waiting = number(environment, "DESK_WAITING", 0, Integer.MAX_VALUE, "a whole number from 0", wrong);
        var seconds = number(environment, "DESK_SECONDS", 1, Integer.MAX_VALUE, "a whole number of seconds from 1", wrong);
        var grace = number(environment, "DESK_GRACE", 0, Integer.MAX_VALUE, "a whole number of seconds from 0", wrong);
        if (!wrong.isEmpty()) {
            throw new IllegalArgumentException(String.join(" ", wrong));
        }
        return new Settings(host, port, running, waiting, Duration.ofSeconds(seconds), grace);
    }

    /** Starts the desk's service with the settings. */
    public static App start(Settings settings, Desk desk, Agent agent, Consumer<String> log) throws IOException {
        var gate = new Gate(settings.running(), settings.waiting(), settings.limit());
        var address = new InetSocketAddress(settings.host(), settings.port());
        return new App(Server.start(address, desk, agent, gate, log), settings.grace());
    }

    /** The address the service listens at. */
    public InetSocketAddress address() {
        return server.getAddress();
    }

    /** Stops taking requests, gives those in flight up to the grace to finish, then interrupts
     * the rest, and returns once every one has ended. */
    public void stop() throws InterruptedException {
        server.stop(grace);
        if (server.getExecutor() instanceof ExecutorService executor) {
            executor.shutdownNow();
            executor.awaitTermination(10, TimeUnit.SECONDS);
        }
    }

    private static String value(Map<String, String> environment, String variable) {
        return environment.getOrDefault(variable, VARIABLES.get(variable));
    }

    private static int number(Map<String, String> environment, String variable, int least, int most, String what,
            ArrayList<String> wrong) {
        var value = value(environment, variable);
        try {
            var number = Integer.parseInt(value);
            if (number >= least && number <= most) {
                return number;
            }
        } catch (NumberFormatException notANumber) {
            // Named below, with the others.
        }
        wrong.add(variable + " is " + what + ", not \"" + value + "\".");
        return least;
    }
}
