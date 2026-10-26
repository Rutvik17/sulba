package tests

import (
	"context"
	"errors"
	"strings"
	"sync"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// granted counts how many of n retries the budget allows, one after another.
func granted(budget *gateway.Budget, n int) int {
	count := 0
	for range n {
		if budget.Retry() {
			count++
		}
	}
	return count
}

var down = &gateway.StatusError{Status: 503, Message: "down"}

// failing gives a call that fails its first n calls with a 503, and counts its calls.
func failing(n int, calls *int) func(context.Context) error {
	return func(context.Context) error {
		*calls++
		if *calls <= n {
			return down
		}
		return nil
	}
}

func TestBudget(t *testing.T) {
	t.Run("tst_n3yikq Allows its floor of retries before any request", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			if got := granted(gateway.NewBudget(0.1, 3, time.Minute), 5); got != 3 {
				t.Errorf("allowed %d of 5 retries, want the floor, 3", got)
			}
		})
	})
	t.Run("tst_2j0c48 Allows its ratio of the window's requests on top", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			budget := gateway.NewBudget(0.1, 2, time.Minute)
			for range 50 {
				budget.Request()
			}
			if got := granted(budget, 10); got != 7 {
				t.Errorf("after 50 requests, allowed %d of 10 retries, want 7: the floor, 2, and a tenth of 50", got)
			}
		})
	})
	t.Run("tst_j273iw Forgets the requests and retries older than its window", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			budget := gateway.NewBudget(0.5, 0, time.Minute)
			for range 4 {
				budget.Request()
			}
			granted(budget, 2)
			time.Sleep(time.Minute)
			budget.Request()
			budget.Request()
			if got := granted(budget, 3); got != 1 {
				t.Errorf("a minute later, after 2 more requests, allowed %d of 3 retries, want 1", got)
			}
		})
	})
	t.Run("tst_5n0qhx Counts every request when many come at once", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			budget := gateway.NewBudget(0.1, 0, time.Minute)
			var group sync.WaitGroup
			for range 100 {
				group.Go(budget.Request)
			}
			group.Wait()
			if got := granted(budget, 15); got != 10 {
				t.Errorf("after 100 requests at once, allowed %d of 15 retries, want a tenth of them, 10", got)
			}
		})
	})
}

func TestRetryWithin(t *testing.T) {
	backoff := gateway.Backoff{Attempts: 3, First: 100 * time.Millisecond, Max: time.Second}
	t.Run("tst_jiwv7a Retries a failed call while the budget allows", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := 0
			err := gateway.RetryWithin(context.Background(), gateway.NewBudget(0.1, 10, time.Minute), backoff, failing(2, &calls))
			if err != nil || calls != 3 {
				t.Errorf("got the error %v after %d calls, want none after 3", err, calls)
			}
		})
	})
	t.Run("tst_2h594j Stops when the budget refuses, with the last error and why", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := 0
			err := gateway.RetryWithin(context.Background(), gateway.NewBudget(0, 0, time.Minute), backoff, failing(5, &calls))
			if !errors.Is(err, down) || calls != 1 {
				t.Fatalf("got the error %v after %d calls, want the 503 after 1", err, calls)
			}
			if !strings.Contains(err.Error(), "retry budget") {
				t.Errorf("got the message %q, want it to say the retry budget was spent", err.Error())
			}
		})
	})
	t.Run("tst_nmqavb Asks the budget before it waits", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := 0
			start := time.Now()
			gateway.RetryWithin(context.Background(), gateway.NewBudget(0, 0, time.Minute), backoff, failing(5, &calls))
			if waited := time.Since(start); waited != 0 {
				t.Errorf("waited %v for a retry the budget refused, want no wait", waited)
			}
		})
	})
	t.Run("tst_lc282p Waits and stops as Retry does", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			calls := 0
			start := time.Now()
			err := gateway.RetryWithin(context.Background(), gateway.NewBudget(1, 10, time.Minute), backoff, failing(5, &calls))
			if !errors.Is(err, down) || calls != 3 || time.Since(start) != 300*time.Millisecond {
				t.Errorf("got the error %v after %d calls and %v, want the 503 after 3 calls and 300ms", err, calls, time.Since(start))
			}
		})
	})
}
