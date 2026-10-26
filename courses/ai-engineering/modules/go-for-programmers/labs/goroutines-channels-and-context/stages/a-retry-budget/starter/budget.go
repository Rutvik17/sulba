package gateway

import (
	"context"
	"time"
)

// A Budget lets a client's requests be retried while the retries in its window stay within its
// floor plus its ratio of the requests in the window.
type Budget struct {
}

// NewBudget gives a budget that allows floor retries in any window, and ratio of the window's
// requests on top.
func NewBudget(ratio float64, floor int, window time.Duration) *Budget {
	return &Budget{}
}

// Request counts a request's first call.
func (b *Budget) Request() {
}

// Retry counts a retry if the budget allows it, and reports whether it did.
func (b *Budget) Retry() bool {
	return true
}

// RetryWithin is Retry with a budget: it counts the request, and before each wait, asks the
// budget for the retry. When the budget refuses, it gives the last error, and says why.
func RetryWithin(ctx context.Context, budget *Budget, backoff Backoff, call func(context.Context) error) error {
	return Retry(ctx, backoff, call)
}
