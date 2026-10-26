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

// A slow upstream answers each request with its last message after the time its content names,
// such as "3s", and fails a request whose content is "fail". It counts the requests it has at
// once, and those it saw canceled.
type slow struct {
	now, most, canceled atomic.Int64
}

func (s *slow) Name() string {
	return "slow"
}

func (s *slow) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	s.most.Store(max(s.most.Load(), s.now.Add(1)))
	defer s.now.Add(-1)
	content := request.Messages[len(request.Messages)-1].Content
	if content == "fail" {
		time.Sleep(time.Second)
		return gateway.Reply{}, &gateway.StatusError{Status: 503, Message: "down"}
	}
	wait, _ := time.ParseDuration(content)
	select {
	case <-time.After(wait):
		return gateway.Reply{Content: "after " + content}, nil
	case <-ctx.Done():
		s.canceled.Add(1)
		return gateway.Reply{}, ctx.Err()
	}
}

func asking(contents ...string) []gateway.ChatRequest {
	var requests []gateway.ChatRequest
	for _, content := range contents {
		requests = append(requests, gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: content}}})
	}
	return requests
}

func TestGate(t *testing.T) {
	t.Run("tst_2jj7wr Lets no more than its number of calls through at once", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			gate := gateway.NewGate(2)
			var now, most atomic.Int64
			var group sync.WaitGroup
			start := time.Now()
			for range 6 {
				group.Go(func() {
					gate.Do(context.Background(), func(context.Context) error {
						most.Store(max(most.Load(), now.Add(1)))
						time.Sleep(time.Second)
						now.Add(-1)
						return nil
					})
				})
			}
			group.Wait()
			if most.Load() != 2 || time.Since(start) != 3*time.Second {
				t.Errorf("had %d calls at once and took %v, want 2 at once, in 3s", most.Load(), time.Since(start))
			}
		})
	})
	t.Run("tst_ac2p7j Frees its place when a call fails or panics", func(t *testing.T) {
		gate := gateway.NewGate(1)
		failed := errors.New("failed")
		if err := gate.Do(context.Background(), func(context.Context) error { return failed }); err != failed {
			t.Fatalf("got the error %v, want the call's own", err)
		}
		func() {
			defer func() { recover() }()
			gate.Do(context.Background(), func(context.Context) error { panic("stopped") })
		}()
		if got := gate.InFlight(); got != 0 {
			t.Errorf("after a call that failed and one that panicked, %d calls were still in flight, want 0", got)
		}
	})
	t.Run("tst_ac1pvh Stops waiting for room when the caller is done", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			gate := gateway.NewGate(1)
			done := make(chan struct{})
			go func() {
				defer close(done)
				gate.Do(context.Background(), func(context.Context) error {
					time.Sleep(10 * time.Second)
					return nil
				})
			}()
			synctest.Wait()
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()
			ran := false
			start := time.Now()
			err := gate.Do(ctx, func(context.Context) error {
				ran = true
				return nil
			})
			if !errors.Is(err, context.DeadlineExceeded) || ran || time.Since(start) != time.Second {
				t.Errorf("got the error %v after %v, and ran the call: %v; want DeadlineExceeded after 1s, without running it",
					err, time.Since(start), ran)
			}
			<-done
		})
	})
}

func TestChatAll(t *testing.T) {
	t.Run("tst_56lzyy Gives the replies in the requests' order", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			replies, err := gateway.ChatAll(context.Background(), gateway.NewGate(5), &slow{}, asking("3s", "1s", "2s"))
			if err != nil || len(replies) != 3 {
				t.Fatalf("got %d replies and the error %v, want 3 and none", len(replies), err)
			}
			for i, want := range []string{"after 3s", "after 1s", "after 2s"} {
				if replies[i].Content != want {
					t.Errorf("reply %d was %q, want %q", i, replies[i].Content, want)
				}
			}
		})
	})
	t.Run("tst_39dri4 Sends the requests at once, through the gate", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			upstream := &slow{}
			start := time.Now()
			gateway.ChatAll(context.Background(), gateway.NewGate(3), upstream, asking("1s", "1s", "1s", "1s", "1s", "1s"))
			if upstream.most.Load() != 3 || time.Since(start) != 2*time.Second {
				t.Errorf("had %d requests at once and took %v, want 3 at once, in 2s", upstream.most.Load(), time.Since(start))
			}
		})
	})
	t.Run("tst_jf0fxo Cancels the rest at the first error, and gives it once they've stopped", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			upstream := &slow{}
			start := time.Now()
			_, err := gateway.ChatAll(context.Background(), gateway.NewGate(5), upstream, asking("10s", "fail", "10s", "10s"))
			if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.Status != 503 {
				t.Fatalf("got the error %v, want the failed request's 503", err)
			}
			if time.Since(start) != time.Second || upstream.canceled.Load() != 3 || upstream.now.Load() != 0 {
				t.Errorf("returned after %v, with %d canceled and %d still running, want 1s, 3 and 0",
					time.Since(start), upstream.canceled.Load(), upstream.now.Load())
			}
		})
	})
	t.Run("tst_gkjhlr Gives the caller's error once the caller is done", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
			defer cancel()
			_, err := gateway.ChatAll(ctx, gateway.NewGate(2), &slow{}, asking("2s", "2s", "2s"))
			if !errors.Is(err, context.DeadlineExceeded) {
				t.Errorf("got the error %v, want DeadlineExceeded", err)
			}
		})
	})
}
