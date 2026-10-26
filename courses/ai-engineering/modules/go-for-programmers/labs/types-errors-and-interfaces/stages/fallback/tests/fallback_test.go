package tests

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// A fake upstream gives its reply or its error, and counts its calls. One that waits gives its
// caller's error once the caller is done.
type fake struct {
	name  string
	reply gateway.Reply
	err   error
	waits bool
	calls int
}

func (f *fake) Name() string {
	return f.name
}

func (f *fake) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	f.calls++
	if f.waits {
		<-ctx.Done()
		return gateway.Reply{}, ctx.Err()
	}
	return f.reply, f.err
}

var hello = gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: "Hi"}}}

func status(code int) error {
	return &gateway.StatusError{Status: code, Message: "said no"}
}

func TestFallback(t *testing.T) {
	t.Run("tst_yjbbv6 Gives the first upstream's reply, and asks no other", func(t *testing.T) {
		a := &fake{name: "a", reply: gateway.Reply{Content: "Hello", PromptTokens: 9, ReplyTokens: 2}}
		b := &fake{name: "b", reply: gateway.Reply{Content: "Hi there"}}
		reply, err := gateway.Fallback(context.Background(), []gateway.Upstream{a, b}, hello)
		if err != nil || reply.Content != "Hello" || reply.PromptTokens != 9 || reply.ReplyTokens != 2 {
			t.Fatalf("got %+v and the error %v, want a's reply", reply, err)
		}
		if b.calls != 0 {
			t.Errorf("b was asked %d times, want none", b.calls)
		}
	})
	t.Run("tst_8d5v5z Names the upstream that replied", func(t *testing.T) {
		a := &fake{name: "a", err: status(503)}
		b := &fake{name: "b", reply: gateway.Reply{Content: "Hello"}}
		reply, err := gateway.Fallback(context.Background(), []gateway.Upstream{a, b}, hello)
		if err != nil || reply.Upstream != "b" {
			t.Errorf("got the upstream %q and the error %v, want b", reply.Upstream, err)
		}
	})
	t.Run("tst_priacy Goes on past an upstream that's busy or failing", func(t *testing.T) {
		a := &fake{name: "a", err: status(503)}
		b := &fake{name: "b", err: status(429)}
		c := &fake{name: "c", err: fmt.Errorf("asking c: %w", context.DeadlineExceeded)}
		d := &fake{name: "d", reply: gateway.Reply{Content: "Hello"}}
		reply, err := gateway.Fallback(context.Background(), []gateway.Upstream{a, b, c, d}, hello)
		if err != nil || reply.Content != "Hello" {
			t.Fatalf("got %+v and the error %v, want d's reply", reply, err)
		}
		if a.calls != 1 || b.calls != 1 || c.calls != 1 || d.calls != 1 {
			t.Errorf("asked a, b, c and d %d, %d, %d and %d times, want once each", a.calls, b.calls, c.calls, d.calls)
		}
	})
	t.Run("tst_qoxyca Stops at an error another upstream wouldn't fix", func(t *testing.T) {
		a := &fake{name: "a", err: status(400)}
		b := &fake{name: "b", reply: gateway.Reply{Content: "Hello"}}
		_, err := gateway.Fallback(context.Background(), []gateway.Upstream{a, b}, hello)
		if refused, ok := errors.AsType[*gateway.StatusError](err); !ok || refused.Status != 400 {
			t.Fatalf("got the error %v, want one with a's StatusError, 400", err)
		}
		if b.calls != 0 {
			t.Errorf("b was asked %d times, want none", b.calls)
		}
	})
	t.Run("tst_ztv53q Joins the errors when every upstream fails, each with its name", func(t *testing.T) {
		a := &fake{name: "a", err: status(503)}
		b := &fake{name: "b", err: status(429)}
		_, err := gateway.Fallback(context.Background(), []gateway.Upstream{a, b}, hello)
		if _, ok := errors.AsType[*gateway.StatusError](err); !ok {
			t.Fatalf("got the error %v, want one with the upstreams' StatusErrors", err)
		}
		for _, want := range []string{"upstream a", "503", "upstream b", "429"} {
			if !strings.Contains(fmt.Sprint(err), want) {
				t.Errorf("got the message %q, want it to say %q", fmt.Sprint(err), want)
			}
		}
	})
	t.Run("tst_t6xjub Stops once the caller's deadline passes", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			a := &fake{name: "a", waits: true}
			b := &fake{name: "b", reply: gateway.Reply{Content: "Hello"}}
			_, err := gateway.Fallback(ctx, []gateway.Upstream{a, b}, hello)
			if !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("got the error %v, want one that wraps context.DeadlineExceeded", err)
			}
			if b.calls != 0 {
				t.Errorf("b was asked %d times after the deadline, want none", b.calls)
			}
		})
	})
	t.Run("tst_cll2st Asks no upstream when there's none, or the caller has gone", func(t *testing.T) {
		if _, err := gateway.Fallback(context.Background(), nil, hello); !errors.Is(err, gateway.ErrNoUpstreams) {
			t.Errorf("with no upstreams, got the error %v, want ErrNoUpstreams", err)
		}
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		a := &fake{name: "a", reply: gateway.Reply{Content: "Hello"}}
		_, err := gateway.Fallback(ctx, []gateway.Upstream{a}, hello)
		if !errors.Is(err, context.Canceled) || a.calls != 0 {
			t.Errorf("for a caller that had gone, got the error %v and %d calls, want context.Canceled and none", err, a.calls)
		}
	})
	t.Run("tst_w8c9dv Says which errors another upstream might fix", func(t *testing.T) {
		for err, want := range map[error]bool{
			status(429):                      true,
			status(500):                      true,
			status(503):                      true,
			fmt.Errorf("b: %w", status(502)): true,
			context.DeadlineExceeded:         true,
			status(400):                      false,
			status(404):                      false,
			errors.New("bad gateway"):        false,
		} {
			if got := gateway.Retryable(err); got != want {
				t.Errorf("for %v, got %v, want %v", err, got, want)
			}
		}
	})
}
