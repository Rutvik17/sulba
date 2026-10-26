package tests

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// allowed counts how many of n requests the bucket lets through, one after another.
func allowed(bucket *gateway.Bucket, n int) int {
	count := 0
	for range n {
		if bucket.Allow() {
			count++
		}
	}
	return count
}

func TestBucket(t *testing.T) {
	t.Run("tst_xgulf3 Starts full, and lets a burst through at once", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(1, 5)
			if got := allowed(bucket, 8); got != 5 {
				t.Errorf("let %d of 8 requests through, want the burst, 5", got)
			}
		})
	})
	t.Run("tst_3pizcc Gains tokens at its rate", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(2, 4)
			allowed(bucket, 4)
			time.Sleep(time.Second)
			if got := allowed(bucket, 3); got != 2 {
				t.Errorf("a second after it was empty, let %d of 3 through, want 2", got)
			}
			time.Sleep(250 * time.Millisecond)
			if bucket.Allow() {
				t.Errorf("a quarter of a second later, with half a token, let a request through")
			}
		})
	})
	t.Run("tst_mo5l2q Holds no more than its burst", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(10, 3)
			time.Sleep(time.Hour)
			if got := allowed(bucket, 10); got != 3 {
				t.Errorf("after an hour idle, let %d of 10 through, want the burst, 3", got)
			}
		})
	})
	t.Run("tst_lyowin Waits for the next token", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(4, 1)
			bucket.Allow()
			start := time.Now()
			if err := bucket.Wait(context.Background()); err != nil {
				t.Fatalf("got the error %v, want none", err)
			}
			if waited := time.Since(start); waited != 250*time.Millisecond {
				t.Errorf("waited %v, want 250ms, a quarter of a second at 4 tokens a second", waited)
			}
		})
	})
	t.Run("tst_rnsjg9 Stops waiting when the caller is done, and takes no token", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(1, 1)
			bucket.Allow()
			ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
			defer cancel()
			start := time.Now()
			err := bucket.Wait(ctx)
			if !errors.Is(err, context.DeadlineExceeded) || time.Since(start) != 100*time.Millisecond {
				t.Fatalf("got the error %v after %v, want DeadlineExceeded after 100ms", err, time.Since(start))
			}
			time.Sleep(900 * time.Millisecond)
			if !bucket.Allow() {
				t.Errorf("a second after it was empty, the bucket had no token: the wait that gave up took one")
			}
		})
	})
	t.Run("tst_vgke5s Lets exactly its burst through when many ask at once", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			bucket := gateway.NewBucket(0.001, 10)
			var through atomic.Int64
			var group sync.WaitGroup
			for range 50 {
				group.Go(func() {
					if bucket.Allow() {
						through.Add(1)
					}
				})
			}
			group.Wait()
			if got := through.Load(); got != 10 {
				t.Errorf("let %d of 50 at once through, want 10", got)
			}
		})
	})
	t.Run("tst_npxgdd Gives each key a bucket of its own", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			limiter := gateway.NewLimiter(1, 2)
			a := limiter.For("key-a")
			if limiter.For("key-a") != a {
				t.Fatalf("gave key-a a second bucket, want the same one each time")
			}
			allowed(a, 2)
			if got := allowed(limiter.For("key-b"), 3); got != 2 {
				t.Errorf("with key-a's bucket empty, key-b's let %d of 3 through, want 2", got)
			}
		})
	})
}
