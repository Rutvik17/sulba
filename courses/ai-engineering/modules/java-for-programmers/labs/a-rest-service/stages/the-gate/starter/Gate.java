import java.time.Duration;

/** The gate in front of the desk's model: how many replies run at once, how many callers wait in
 * line for a place, and how long each reply has. */
public final class Gate {
    /** The gate turned a caller away, with the line full: they can try again after
     * {@code retryAfter} seconds. */
    public static final class Busy extends Exception {
        public Busy(long retryAfter) {}

        public long retryAfter() {
            throw new UnsupportedOperationException("Not written yet.");
        }
    }

    public Gate(int running, int waiting, Duration limit) {}

    /** How long each reply has. */
    public Duration limit() {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Takes a running place, waiting in line for one if the line has room, or throws Busy. */
    public void enter() throws Busy, InterruptedException {
        throw new UnsupportedOperationException("Not written yet.");
    }

    /** Gives a running place back, to the next caller in line. */
    public void leave() {
        throw new UnsupportedOperationException("Not written yet.");
    }
}
