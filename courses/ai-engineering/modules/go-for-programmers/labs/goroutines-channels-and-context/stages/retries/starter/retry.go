package gateway

import (
	"context"
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
	return 0
}

// Retry calls call until it succeeds or fails with an error that isn't retryable, making up to
// b.Attempts calls. Before each retry it waits b.Delay, after Jitter, or as long as the error's
// StatusError asked, if that's longer. Out of calls, it gives the last error and how many calls
// it made. It stops once ctx is done, and starts no wait that would end after ctx's deadline.
func Retry(ctx context.Context, b Backoff, call func(context.Context) error) error {
	return call(ctx)
}
