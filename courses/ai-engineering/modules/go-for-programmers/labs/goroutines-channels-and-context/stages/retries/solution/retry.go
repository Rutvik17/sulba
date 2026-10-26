package gateway

import (
	"context"
	"errors"
	"fmt"
	"time"
)

// A Backoff says how many calls to make, and how long to wait before each retry: First before the
// first retry, twice as long before each one after, up to Max. Jitter, when it's set, changes
// each wait, such as to spread out retries that would otherwise come at once.
type Backoff struct {
	Attempts int
	First    time.Duration
	Max      time.Duration
	Jitter   func(time.Duration) time.Duration
}

// Delay gives the wait before retry n, counting from 1, before Jitter changes it.
func (b Backoff) Delay(n int) time.Duration {
	delay := b.First
	for range n - 1 {
		if delay >= b.Max/2 {
			return b.Max
		}
		delay *= 2
	}
	return min(delay, b.Max)
}

// Retry calls call until it succeeds or fails with an error that isn't retryable, making up to
// b.Attempts calls. Before each retry it waits b.Delay, after Jitter, or as long as the error's
// StatusError asked, if that's longer. Out of calls, it gives the last error and how many calls
// it made. It stops once ctx is done, and starts no wait that would end after ctx's deadline.
func Retry(ctx context.Context, b Backoff, call func(context.Context) error) error {
	for attempt := 1; ; attempt++ {
		err := call(ctx)
		if err == nil || !Retryable(err) {
			return err
		}
		if attempt >= b.Attempts {
			return fmt.Errorf("after %d calls: %w", attempt, err)
		}
		wait := b.Delay(attempt)
		if b.Jitter != nil {
			wait = b.Jitter(wait)
		}
		if status, ok := errors.AsType[*StatusError](err); ok && status.RetryAfter > wait {
			wait = status.RetryAfter
		}
		if deadline, ok := ctx.Deadline(); ok && time.Until(deadline) < wait {
			return fmt.Errorf("after %d calls, with no time for another: %w", attempt, err)
		}
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
			return errors.Join(ctx.Err(), err)
		case <-timer.C:
		}
	}
}
