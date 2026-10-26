package checks

import (
	"context"
	"errors"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// A timed upstream gives its reply or its error after its wait. One that listens gives up when
// its caller is done, and says so on canceled.
type timed struct {
	name     string
	wait     time.Duration
	err      error
	listens  bool
	canceled chan struct{}
}

func (u *timed) Name() string {
	return u.name
}

func (u *timed) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	if !u.listens {
		time.Sleep(u.wait)
		return gateway.Reply{Content: "from " + u.name}, u.err
	}
	select {
	case <-time.After(u.wait):
		return gateway.Reply{Content: "from " + u.name}, u.err
	case <-ctx.Done():
		close(u.canceled)
		return gateway.Reply{}, ctx.Err()
	}
}

var hello = gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: "Hi"}}}

func TestFanoutInUse(t *testing.T) {
	t.Run("tst_f73z28 Leaves no goroutine behind", func(t *testing.T) {
		defer func() {
			if stopped := recover(); stopped != nil {
				t.Errorf("goroutines were still blocked after every upstream had answered: %v", stopped)
			}
		}()
		synctest.Test(t, func(t *testing.T) {
			upstreams := []gateway.Upstream{
				&timed{name: "a", wait: time.Second},
				&timed{name: "b", wait: 2 * time.Second},
				&timed{name: "c", wait: 3 * time.Second},
			}
			if reply, err := gateway.Fanout(context.Background(), upstreams, hello); err != nil || reply.Upstream != "a" {
				t.Errorf("got %+v and the error %v, want a's reply", reply, err)
			}
			time.Sleep(5 * time.Second)
		})
	})
	t.Run("tst_0d7ot1 Cancels the upstreams it no longer needs", func(t *testing.T) {
		slow := &timed{name: "slow", wait: 10 * time.Second, listens: true, canceled: make(chan struct{})}
		upstreams := []gateway.Upstream{&timed{name: "quick"}, slow}
		if reply, err := gateway.Fanout(context.Background(), upstreams, hello); err != nil || reply.Upstream != "quick" {
			t.Fatalf("got %+v and the error %v, want quick's reply", reply, err)
		}
		select {
		case <-slow.canceled:
		case <-time.After(2 * time.Second):
			t.Errorf("2 seconds after quick replied, slow was still being asked")
		}
	})
	t.Run("tst_gtwg7t Waits past an upstream that fails for one that replies", func(t *testing.T) {
		defer func() {
			if stopped := recover(); stopped != nil {
				t.Errorf("Fanout returned before every upstream had answered: %v", stopped)
			}
		}()
		synctest.Test(t, func(t *testing.T) {
			down := &gateway.StatusError{Status: 503, Message: "down"}
			upstreams := []gateway.Upstream{
				&timed{name: "failing", err: down},
				&timed{name: "working", wait: 100 * time.Millisecond},
			}
			if reply, err := gateway.Fanout(context.Background(), upstreams, hello); err != nil || reply.Upstream != "working" {
				t.Errorf("got %+v and the error %v, want working's reply", reply, err)
			}
		})
	})
	t.Run("tst_xe2nrq Gives up at the caller's deadline", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
		defer cancel()
		start := time.Now()
		_, err := gateway.Fanout(ctx, []gateway.Upstream{&timed{name: "stuck", wait: 3 * time.Second}}, hello)
		if !errors.Is(err, context.DeadlineExceeded) || time.Since(start) > time.Second {
			t.Errorf("got the error %v after %v, want DeadlineExceeded at the 100ms deadline", err, time.Since(start).Round(time.Millisecond))
		}
	})
}
