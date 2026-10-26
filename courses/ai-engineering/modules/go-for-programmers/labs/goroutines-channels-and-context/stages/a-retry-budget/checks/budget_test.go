package checks

import (
	"context"
	"sync"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// A call the traffic made: when, after the traffic began, which request made it, and which of
// the request's calls it was, from 1.
type call struct {
	at      time.Duration
	request int
	attempt int
}

var (
	backoff = gateway.Backoff{Attempts: 3, First: 100 * time.Millisecond, Max: time.Second}
	down    = &gateway.StatusError{Status: 503, Message: "down"}
)

// traffic sends n requests, one each gap, through RetryWithin with budget. fails says whether
// each request's call fails, by the request's number and the call's, from 1. It gives each
// request's error, and every call.
func traffic(budget *gateway.Budget, n int, gap time.Duration, fails func(request, attempt int) bool) ([]error, []call) {
	var mu sync.Mutex
	var calls []call
	errs := make([]error, n)
	start := time.Now()
	var group sync.WaitGroup
	for request := range n {
		group.Go(func() {
			attempt := 0
			errs[request] = gateway.RetryWithin(context.Background(), budget, backoff, func(context.Context) error {
				attempt++
				mu.Lock()
				calls = append(calls, call{at: time.Since(start), request: request, attempt: attempt})
				mu.Unlock()
				if fails(request+1, attempt) {
					return down
				}
				return nil
			})
		})
		time.Sleep(gap)
	}
	group.Wait()
	return errs, calls
}

func TestBudgetUnderLoad(t *testing.T) {
	t.Run("tst_2hrmkc Holds an outage's retries to the budget", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			ratio, floor, window := 0.1, 10, time.Minute
			_, calls := traffic(gateway.NewBudget(ratio, floor, window), 1000, 100*time.Millisecond, func(int, int) bool { return true })
			// A call takes no time here, so the budget allows each retry the moment the call before
			// it fails: at that call's time.
			previous := map[[2]int]time.Duration{}
			for _, each := range calls {
				previous[[2]int{each.request, each.attempt + 1}] = each.at
			}
			allowed := func(each call) time.Duration { return previous[[2]int{each.request, each.attempt}] }
			for _, each := range calls {
				if each.attempt == 1 {
					continue
				}
				at := allowed(each)
				// Those the budget had counted by then, at the least: the requests up to that
				// moment, and the retries it allowed before it.
				requests, retries := 0, 1
				for _, other := range calls {
					if other.attempt == 1 && other.at > at-window && other.at <= at {
						requests++
					} else if other.attempt > 1 && allowed(other) > at-window && allowed(other) < at {
						retries++
					}
				}
				if float64(retries) > float64(floor)+ratio*float64(requests) {
					t.Fatalf("at %v, the last minute had %d retries for %d requests, more than 10 and a tenth of them", at, retries, requests)
				}
			}
		})
	})
	t.Run("tst_torijy Keeps the retries of healthy traffic", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			errs, _ := traffic(gateway.NewBudget(0.1, 10, time.Minute), 1000, 100*time.Millisecond, func(request, attempt int) bool {
				return request%20 == 0 && attempt == 1
			})
			for request, err := range errs {
				if err != nil {
					t.Fatalf("request %d, one of the 1 in 20 whose first call failed, got the error %v, want its retry to succeed", request+1, err)
				}
			}
		})
	})
	t.Run("tst_6s8fhq Retries again once an outage has left the window", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			budget := gateway.NewBudget(0.1, 10, time.Minute)
			traffic(budget, 300, 100*time.Millisecond, func(int, int) bool { return true })
			time.Sleep(time.Minute)
			errs, _ := traffic(budget, 1, 0, func(request, attempt int) bool { return attempt == 1 })
			if errs[0] != nil {
				t.Errorf("a minute after the outage, a request whose first call failed got the error %v, want its retry to succeed", errs[0])
			}
		})
	})
	t.Run("tst_1539zm Still makes no more calls than the backoff's attempts", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			_, calls := traffic(gateway.NewBudget(1, 1000, time.Minute), 10, time.Second, func(int, int) bool { return true })
			if len(calls) != 30 {
				t.Errorf("10 requests that always failed made %d calls with budget to spare, want 3 each, 30", len(calls))
			}
		})
	})
}
