import java.time.Duration;
import java.util.concurrent.Semaphore;

/** The gate in front of the desk's model: how many replies run at once, how many callers wait in
 * line for a place, and how long each reply has. */
public final class Gate {
    /** The gate turned a caller away, with the line full: they can try again after
     * {@code retryAfter} seconds. */
    public static final class Busy extends Exception {
        private final long retryAfter;

        public Busy(long retryAfter) {
            super("The line is full: try again in " + retryAfter + " seconds.");
            this.retryAfter = retryAfter;
        }

        public long retryAfter() {
            return retryAfter;
        }
    }

    private final Semaphore running;
    // A permit for each running place and each place in line, taken without waiting.
    private final Semaphore inside;
    private final Duration limit;

    public Gate(int running, int waiting, Duration limit) {
        if (running < 1) {
            throw new IllegalArgumentException("A gate lets at least 1 reply run, not " + running + ".");
        }
        if (waiting < 0) {
            throw new IllegalArgumentException("A gate's line holds 0 callers or more, not " + waiting + ".");
        }
        if (!limit.isPositive()) {
            throw new IllegalArgumentException("A reply's limit is longer than no time, not " + limit + ".");
        }
        this.running = new Semaphore(running, true);
        this.inside = new Semaphore(running + waiting);
        this.limit = limit;
    }

    /** How long each reply has. */
    public Duration limit() {
        return limit;
    }

    /** Takes a running place, waiting in line for one if the line has room, or throws Busy. */
    public void enter() throws Busy, InterruptedException {
        if (!inside.tryAcquire()) {
            throw new Busy(limit.toNanosPart() == 0 ? limit.toSeconds() : limit.toSeconds() + 1);
        }
        try {
            running.acquire();
        } catch (InterruptedException interrupted) {
            inside.release();
            throw interrupted;
        }
    }

    /** Gives a running place back, to the next caller in line. */
    public void leave() {
        running.release();
        inside.release();
    }
}
