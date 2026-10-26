import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class GateTest {
    static final Duration MINUTE = Duration.ofSeconds(60);
    static final Duration SOON = Duration.ofSeconds(10);

    /** A caller on a thread of their own, who enters the gate and notes it in {@code entered}. */
    static Thread caller(Gate gate, String name, ConcurrentLinkedQueue<String> entered, AtomicReference<Exception> error) {
        return Thread.ofVirtual().start(() -> {
            try {
                gate.enter();
                entered.add(name);
            } catch (Gate.Busy | InterruptedException failed) {
                error.set(failed);
            }
        });
    }

    /** Waits until the thread is waiting, as a caller in line does. */
    static void awaitWaiting(Thread thread) throws InterruptedException {
        var deadline = System.nanoTime() + SOON.toNanos();
        while (thread.getState() != Thread.State.WAITING) {
            if (System.nanoTime() > deadline) {
                fail("The caller never waited in line.");
            }
            Thread.sleep(5);
        }
    }

    static void awaitEnd(Thread thread) throws InterruptedException {
        assertTrue(thread.join(SOON), "The caller is still waiting.");
    }

    @Test
    @DisplayName("tst_3bsihz Lets as many replies run at once as it has places")
    void places() {
        var gate = new Gate(2, 0, MINUTE);
        assertEquals(MINUTE, gate.limit());
        assertTimeoutPreemptively(SOON, () -> {
            gate.enter();
            gate.enter();
        });
    }

    @Test
    @DisplayName("tst_gs5g9g Turns a caller away when the line is full, saying when to try again")
    void busy() throws Exception {
        var gate = new Gate(1, 1, MINUTE);
        gate.enter();
        var waiting = caller(gate, "second", new ConcurrentLinkedQueue<>(), new AtomicReference<>());
        awaitWaiting(waiting);
        assertEquals(60, assertTimeoutPreemptively(SOON, () -> assertThrows(Gate.Busy.class, gate::enter)).retryAfter());
        for (var limit : List.of(Duration.ofMillis(2500), Duration.ofMillis(100), Duration.ofSeconds(3))) {
            var full = new Gate(1, 0, limit);
            full.enter();
            assertEquals(limit.equals(Duration.ofMillis(100)) ? 1 : 3, assertThrows(Gate.Busy.class, full::enter).retryAfter());
        }
        waiting.interrupt();
    }

    @Test
    @DisplayName("tst_3ct3jp Lets the next caller in line in when a reply leaves")
    void next() throws Exception {
        var gate = new Gate(1, 1, MINUTE);
        var entered = new ConcurrentLinkedQueue<String>();
        gate.enter();
        var waiting = caller(gate, "second", entered, new AtomicReference<>());
        awaitWaiting(waiting);
        assertTrue(entered.isEmpty());
        gate.leave();
        awaitEnd(waiting);
        assertEquals(List.of("second"), List.copyOf(entered));
    }

    @Test
    @DisplayName("tst_2zcfxm Lets callers in, in the order they came")
    void order() throws Exception {
        var gate = new Gate(1, 3, MINUTE);
        var entered = new ConcurrentLinkedQueue<String>();
        gate.enter();
        var second = briefly(gate, "second", entered);
        awaitWaiting(second);
        var third = briefly(gate, "third", entered);
        awaitWaiting(third);
        gate.leave();
        // Back at once for another reply, this caller takes their turn after those in line.
        gate.enter();
        entered.add("first, again");
        gate.leave();
        awaitEnd(second);
        awaitEnd(third);
        assertEquals(List.of("second", "third", "first, again"), List.copyOf(entered));
    }

    /** A caller whose reply ends as soon as it starts. */
    static Thread briefly(Gate gate, String name, ConcurrentLinkedQueue<String> entered) {
        return Thread.ofVirtual().start(() -> {
            try {
                gate.enter();
                entered.add(name);
                gate.leave();
            } catch (Gate.Busy | InterruptedException failed) {
                entered.add(failed.toString());
            }
        });
    }

    @Test
    @DisplayName("tst_sdgl1e A caller who leaves the line gives up their place in it")
    void interrupted() throws Exception {
        var gate = new Gate(1, 1, MINUTE);
        gate.enter();
        var error = new AtomicReference<Exception>();
        var entered = new ConcurrentLinkedQueue<String>();
        var gone = caller(gate, "gone", entered, error);
        awaitWaiting(gone);
        gone.interrupt();
        awaitEnd(gone);
        assertInstanceOf(InterruptedException.class, error.get());
        var next = caller(gate, "next", entered, error);
        awaitWaiting(next);
        gate.leave();
        awaitEnd(next);
        assertEquals(List.of("next"), List.copyOf(entered));
        gate.leave();
        assertTimeoutPreemptively(SOON, gate::enter);
    }

    @Test
    @DisplayName("tst_9lifwv Refuses places, a line or a limit it can't keep")
    void refuses() {
        assertThrows(IllegalArgumentException.class, () -> new Gate(0, 4, MINUTE));
        assertThrows(IllegalArgumentException.class, () -> new Gate(2, -1, MINUTE));
        assertThrows(IllegalArgumentException.class, () -> new Gate(2, 4, Duration.ZERO));
        assertThrows(IllegalArgumentException.class, () -> new Gate(2, 4, Duration.ofSeconds(-5)));
        assertTimeoutPreemptively(SOON, () -> new Gate(1, 0, Duration.ofMillis(1)).enter());
    }

    @Test
    @DisplayName("tst_hoarqp Keeps its count with many callers at once")
    void many() throws Exception {
        var gate = new Gate(3, 1000, MINUTE);
        var inside = new AtomicInteger();
        var most = new AtomicInteger();
        var done = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(30), () -> {
            try (var callers = Executors.newVirtualThreadPerTaskExecutor()) {
                for (var i = 0; i < 500; i++) {
                    callers.submit(() -> {
                        gate.enter();
                        most.accumulateAndGet(inside.incrementAndGet(), Math::max);
                        Thread.sleep(1);
                        inside.decrementAndGet();
                        gate.leave();
                        return done.incrementAndGet();
                    });
                }
            }
        });
        assertEquals(500, done.get());
        assertEquals(3, most.get());
        assertTimeoutPreemptively(SOON, () -> {
            gate.enter();
            gate.enter();
            gate.enter();
        });
        assertFalse(Thread.currentThread().isInterrupted());
    }
}
