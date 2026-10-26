package checks

import (
	"context"
	"errors"
	"sync"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

// A counting upstream answers with the content of a request's first message, or with its
// failures first, one a request, and counts the requests it's asked.
type counting struct {
	failures []error
	asked    int
}

func (c *counting) Name() string {
	return "local"
}

func (c *counting) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	c.asked++
	if len(c.failures) > 0 {
		err := c.failures[0]
		c.failures = c.failures[1:]
		return gateway.Reply{}, err
	}
	return gateway.Reply{Upstream: "local", Content: "about " + request.Messages[0].Content}, nil
}

var errAlone = errors.New("no other request reached the upstream within 2 seconds")

// A meeting upstream replies once two requests are inside it at once, and gives errAlone if the
// second doesn't arrive within 2 seconds.
type meeting struct {
	inside chan struct{}
	both   chan struct{}
	once   sync.Once
}

func (m *meeting) Name() string {
	return "local"
}

func (m *meeting) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	m.inside <- struct{}{}
	if len(m.inside) == cap(m.inside) {
		m.once.Do(func() { close(m.both) })
	}
	select {
	case <-m.both:
		return gateway.Reply{Upstream: "local", Content: "Hello"}, nil
	case <-time.After(2 * time.Second):
		return gateway.Reply{}, errAlone
	}
}

func ask(contents ...string) gateway.ChatRequest {
	request := gateway.ChatRequest{Model: "qwen"}
	for i, content := range contents {
		role := "user"
		if i%2 == 1 {
			role = "assistant"
		}
		request.Messages = append(request.Messages, gateway.Message{Role: role, Content: content})
	}
	return request
}

func TestCacheInUse(t *testing.T) {
	t.Run("tst_6fyx63 Asks its upstream again once a reply's time to live is up", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			upstream := &counting{}
			cache := gateway.NewCache(upstream, time.Minute)
			cache.Chat(context.Background(), ask("Hi"))
			time.Sleep(2 * time.Minute)
			cache.Chat(context.Background(), ask("Hi"))
			if upstream.asked != 2 {
				t.Errorf("the upstream had %d requests for one asked twice, 2 minutes apart with a minute to live, want 2", upstream.asked)
			}
		})
	})
	t.Run("tst_wt7496 Lets different requests reach its upstream at once", func(t *testing.T) {
		cache := gateway.NewCache(&meeting{inside: make(chan struct{}, 2), both: make(chan struct{})}, time.Minute)
		errs := make(chan error, 2)
		for _, content := range []string{"Hi", "Hello"} {
			go func() {
				_, err := cache.Chat(context.Background(), ask(content))
				errs <- err
			}()
		}
		for range 2 {
			if err := <-errs; err != nil {
				t.Errorf("got the error %v, want both requests inside the upstream at once", err)
			}
		}
	})
	t.Run("tst_8lpujp Asks its upstream again after a failure", func(t *testing.T) {
		upstream := &counting{failures: []error{&gateway.StatusError{Status: 503, Message: "down"}}}
		cache := gateway.NewCache(upstream, time.Minute)
		if _, err := cache.Chat(context.Background(), ask("Hi")); err == nil {
			t.Fatalf("got no error, want the upstream's 503 the first time")
		}
		if reply, err := cache.Chat(context.Background(), ask("Hi")); err != nil || reply.Content != "about Hi" {
			t.Errorf("got %+v and the error %v the second time, want the upstream's reply, about Hi", reply, err)
		}
	})
	t.Run("tst_toplsu Keeps conversations that end alike apart", func(t *testing.T) {
		cache := gateway.NewCache(&counting{}, time.Minute)
		paris, _ := cache.Chat(context.Background(), ask("Tell me about Paris", "Paris is the capital of France.", "How many people live there?"))
		lyon, err := cache.Chat(context.Background(), ask("Tell me about Lyon", "Lyon is a city in France.", "How many people live there?"))
		if err != nil || lyon.Content != "about Tell me about Lyon" {
			t.Errorf("got %+v and the error %v for Lyon after %+v for Paris, want Lyon's own reply", lyon, err, paris)
		}
	})
}
