package gateway;

import java.time.Duration;
import java.time.InstantSource;

/** A token bucket that refills from the clock it's given, so a test can move time itself. */
public final class Bucket {
    private final InstantSource clock;
    private final double rate;
    private final int burst;
    private double tokens;
    private long last;

    public Bucket(InstantSource clock, double rate, int burst) {
        this.clock = clock;
        this.rate = rate;
        this.burst = burst;
        this.tokens = burst;
        this.last = clock.millis();
    }

    public synchronized boolean allow() {
        long now = clock.millis();
        tokens = Math.min(burst, tokens + (now - last) / 1000.0 * rate);
        last = now;
        if (tokens < 1) {
            return false;
        }
        tokens -= 1;
        return true;
    }

    public static Duration wait(int tokens, double rate) {
        return Duration.ofMillis((long) (tokens / rate * 1000));
    }
}
