package gateway

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// A Budget lets a client's requests be retried while the retries in its window stay within its
// floor plus its ratio of the requests in the window.
type Budget struct {
	mu       sync.Mutex
	ratio    float64
	floor    int
	window   time.Duration
	requests []time.Time
	retries  []time.Time
}

// NewBudget gives a budget that allows floor retries in any window, and ratio of the window's
// requests on top.
func NewBudget(ratio float64, floor int, window time.Duration) *Budget {
	return &Budget{ratio: ratio, floor: floor, window: window}
}

// recent gives the times in the window that ends now. The caller holds b.mu.
func (b *Budget) recent(times []time.Time, now time.Time) []time.Time {
	start := now.Add(-b.window)
	kept := 0
	for kept < len(times) && !times[kept].After(start) {
		kept++
	}
	return times[kept:]
}

// Request counts a request's first call.
func (b *Budget) Request() {
	b.mu.Lock()
	defer b.mu.Unlock()
	now := time.Now()
	b.requests = append(b.recent(b.requests, now), now)
}

// Retry counts a retry if the budget allows it, and reports whether it did.
func (b *Budget) Retry() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	now := time.Now()
	b.requests = b.recent(b.requests, now)
	b.retries = b.recent(b.retries, now)
	if float64(len(b.retries)+1) > float64(b.floor)+b.ratio*float64(len(b.requests)) {
		return false
	}
	b.retries = append(b.retries, now)
	return true
}

// RetryWithin is Retry with a budget: it counts the request, and before each wait, asks the
// budget for the retry. When the budget refuses, it gives the last error, and says why.
func RetryWithin(ctx context.Context, budget *Budget, backoff Backoff, call func(context.Context) error) error {
	budget.Request()
	for attempt := 1; ; attempt++ {
		err := call(ctx)
		if err == nil || !Retryable(err) {
			return err
		}
		if attempt >= backoff.Attempts {
			return fmt.Errorf("after %d calls: %w", attempt, err)
		}
		wait := backoff.Delay(attempt)
		if backoff.Jitter != nil {
			wait = backoff.Jitter(wait)
		}
		if status, ok := errors.AsType[*StatusError](err); ok && status.RetryAfter > wait {
			wait = status.RetryAfter
		}
		if deadline, ok := ctx.Deadline(); ok && time.Until(deadline) < wait {
			return fmt.Errorf("after %d calls, with no time for another: %w", attempt, err)
		}
		if !budget.Retry() {
			return fmt.Errorf("after %d calls, with no retry budget left: %w", attempt, err)
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
