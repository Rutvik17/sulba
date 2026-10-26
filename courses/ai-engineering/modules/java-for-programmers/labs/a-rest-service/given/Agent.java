import java.time.Duration;
import java.util.concurrent.TimeoutException;

/** The desk's agent, which replies to a caller's message as its model writes the reply. */
public interface Agent {
    /** What a reply gives as it's written: its text a piece at a time, each tool the agent runs,
     * and last, the whole reply. */
    sealed interface Event permits Text, Tool, Done {}

    /** A piece of the reply's text. */
    record Text(String delta) implements Event {}

    /** A tool the agent runs, by its name. */
    record Tool(String name) implements Event {}

    /** The whole reply, once it's written. */
    record Done(String content) implements Event {}

    /** The model failed, or the agent gave up, before the reply was whole. */
    final class Failed extends Exception {
        public Failed(String message) {
            super(message);
        }
    }

    /** A reply as it's written. Closing it stops the agent writing it. */
    interface Reply extends AutoCloseable {
        /** The reply's next event, once it comes. If none comes within {@code wait}, it throws
         * {@code TimeoutException}, and the reply goes on. */
        Event next(Duration wait) throws Failed, TimeoutException, InterruptedException;

        @Override
        void close();
    }

    /** Starts a reply to the caller's message. */
    Reply reply(String message);
}
