package tests

import (
	"context"
	"errors"
	"testing"
	"time"

	"example/gateway"
)

// A counting upstream answers every request with its reply or its error, and counts the
// requests it's asked.
type counting struct {
	reply gateway.Reply
	err   error
	asked int
}

func (c *counting) Name() string {
	return "local"
}

func (c *counting) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	c.asked++
	return c.reply, c.err
}

func ask(content string) gateway.ChatRequest {
	return gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: content}}}
}

func TestCache(t *testing.T) {
	t.Run("tst_sewazy Answers a request it has seen from the cache", func(t *testing.T) {
		upstream := &counting{reply: gateway.Reply{Upstream: "local", Content: "Hello"}}
		cache := gateway.NewCache(upstream, time.Minute)
		for range 3 {
			if reply, err := cache.Chat(context.Background(), ask("Hi")); err != nil || reply.Content != "Hello" {
				t.Fatalf("got %+v and the error %v, want Hello", reply, err)
			}
		}
		if upstream.asked != 1 {
			t.Errorf("the upstream had %d requests for one asked 3 times, want 1", upstream.asked)
		}
	})
	t.Run("tst_2uodop Asks its upstream for a request it hasn't seen", func(t *testing.T) {
		upstream := &counting{reply: gateway.Reply{Upstream: "local", Content: "Hello"}}
		cache := gateway.NewCache(upstream, time.Minute)
		cache.Chat(context.Background(), ask("Hi"))
		cache.Chat(context.Background(), ask("Hello"))
		if upstream.asked != 2 {
			t.Errorf("the upstream had %d requests for two different ones, want 2", upstream.asked)
		}
	})
	t.Run("tst_9zju7a Gives its upstream's error", func(t *testing.T) {
		down := &gateway.StatusError{Status: 503, Message: "down"}
		cache := gateway.NewCache(&counting{err: down}, time.Minute)
		if _, err := cache.Chat(context.Background(), ask("Hi")); !errors.Is(err, down) {
			t.Errorf("got the error %v, want the upstream's 503", err)
		}
	})
	t.Run("tst_yovp68 Has its upstream's name", func(t *testing.T) {
		if name := gateway.NewCache(&counting{}, time.Minute).Name(); name != "local" {
			t.Errorf("got the name %q, want local", name)
		}
	})
}
