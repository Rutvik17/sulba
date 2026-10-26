package tests

import (
	"context"
	"errors"
	"slices"
	"strings"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// A script answers each call with the next of its errors, then with success, and keeps how long
// after it was made each call came.
type script struct {
	errs  []error
	start time.Time
	times []time.Duration
}

func newScript(errs ...error) *script {
	return &script{errs: errs, start: time.Now()}
}

func (s *script) call(ctx context.Context) error {
	s.times = append(s.times, time.Since(s.start))
	if len(s.times) <= len(s.errs) {
		return s.errs[len(s.times)-1]
	}
	return nil
}

func busy(wait time.Duration) error {
	return &gateway.StatusError{Status: 429, Message: "busy", RetryAfter: wait}
}

var down = &gateway.StatusError{Status: 503, Message: "down"}

func ms(values ...int) []time.Duration {
	var times []time.Duration
	for _, each := range values {
		times = append(times, time.Duration(each)*time.Millisecond)
	}
	return times
}

func TestRetry(t *testing.T) {
	backoff := gateway.Backoff{Attempts: 5, First: 100 * time.Millisecond, Max: 10 * time.Second}
	t.Run("tst_9qezjw Calls once when the call succeeds", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := newScript()
			if err := gateway.Retry(context.Background(), backoff, calls.call); err != nil || len(calls.times) != 1 {
				t.Errorf("got the error %v after %d calls, want none after 1", err, len(calls.times))
			}
		})
	})
	t.Run("tst_fbq3df Waits First, then twice as long before each retry", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := newScript(down, down, down)
			if err := gateway.Retry(context.Background(), backoff, calls.call); err != nil {
				t.Fatalf("got the error %v, want none", err)
			}
			if want := ms(0, 100, 300, 700); !slices.Equal(calls.times, want) {
				t.Errorf("called at %v, want %v", calls.times, want)
			}
		})
	})
	t.Run("tst_edu9if Waits no longer than Max", func(t *testing.T) {
		capped := gateway.Backoff{Attempts: 10, First: time.Second, Max: 5 * time.Second}
		var got []time.Duration
		for n := 1; n <= 6; n++ {
			got = append(got, capped.Delay(n))
		}
		if want := ms(1000, 2000, 4000, 5000, 5000, 5000); !slices.Equal(got, want) {
			t.Errorf("got the delays %v, want %v", got, want)
		}
	})
	t.Run("tst_mg1efi Gives up after Attempts calls, saying how many", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := newScript(down, down, down, down, down)
			three := gateway.Backoff{Attempts: 3, First: 100 * time.Millisecond, Max: time.Second}
			err := gateway.Retry(context.Background(), three, calls.call)
			if _, ok := errors.AsType[*gateway.StatusError](err); !ok || len(calls.times) != 3 {
				t.Fatalf("got the error %v after %d calls, want the 503 after 3", err, len(calls.times))
			}
			if !strings.Contains(err.Error(), "after 3 calls") {
				t.Errorf("got the message %q, want it to say it gave up after 3 calls", err.Error())
			}
		})
	})
	t.Run("tst_il1or3 Doesn't retry an error another call wouldn't fix", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			refused := &gateway.StatusError{Status: 400, Message: "bad request"}
			calls := newScript(refused)
			if err := gateway.Retry(context.Background(), backoff, calls.call); err != refused || len(calls.times) != 1 {
				t.Errorf("got the error %v after %d calls, want the 400 after 1", err, len(calls.times))
			}
		})
	})
	t.Run("tst_5whxx1 Waits as long as the upstream asked, when that's longer", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := newScript(busy(2*time.Second), busy(50*time.Millisecond))
			if err := gateway.Retry(context.Background(), backoff, calls.call); err != nil {
				t.Fatalf("got the error %v, want none", err)
			}
			if want := ms(0, 2000, 2200); !slices.Equal(calls.times, want) {
				t.Errorf("called at %v, want %v", calls.times, want)
			}
		})
	})
	t.Run("tst_rtc7t5 Jitters each wait", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			halved := backoff
			halved.Jitter = func(wait time.Duration) time.Duration { return wait / 2 }
			calls := newScript(down, down)
			if err := gateway.Retry(context.Background(), halved, calls.call); err != nil {
				t.Fatalf("got the error %v, want none", err)
			}
			if want := ms(0, 50, 150); !slices.Equal(calls.times, want) {
				t.Errorf("called at %v, want %v", calls.times, want)
			}
		})
	})
	t.Run("tst_rbbz44 Stops when the caller is done, and starts no wait past its deadline", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 250*time.Millisecond)
			defer cancel()
			calls := newScript(down, down, down)
			err := gateway.Retry(ctx, backoff, calls.call)
			if _, ok := errors.AsType[*gateway.StatusError](err); !ok || len(calls.times) != 2 || time.Since(calls.start) != 100*time.Millisecond {
				t.Errorf("with a 250ms deadline, got the error %v after %d calls and %v, want the 503 after 2 calls and 100ms",
					err, len(calls.times), time.Since(calls.start))
			}
		})
		synctest.Test(t, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			time.AfterFunc(50*time.Millisecond, cancel)
			calls := newScript(down, down)
			err := gateway.Retry(ctx, backoff, calls.call)
			if !errors.Is(err, context.Canceled) || len(calls.times) != 1 || time.Since(calls.start) != 50*time.Millisecond {
				t.Errorf("canceled during a wait, got the error %v after %d calls and %v, want context.Canceled after 1 call and 50ms",
					err, len(calls.times), time.Since(calls.start))
			}
		})
	})
}
