package tests

import (
	"context"
	"errors"
	"testing"

	"example/gateway"
)

// A quick upstream answers at once, with its reply or its error.
type quick struct {
	name  string
	reply gateway.Reply
	err   error
}

func (q quick) Name() string {
	return q.name
}

func (q quick) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	return q.reply, q.err
}

var hello = gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: "Hi"}}}

func TestFanout(t *testing.T) {
	t.Run("tst_onjq12 Gives the reply of the only upstream, with its name", func(t *testing.T) {
		reply, err := gateway.Fanout(context.Background(), []gateway.Upstream{quick{name: "a", reply: gateway.Reply{Content: "Hello"}}}, hello)
		if err != nil || reply.Content != "Hello" || reply.Upstream != "a" {
			t.Errorf("got %+v and the error %v, want a's Hello", reply, err)
		}
	})
	t.Run("tst_vwcosq Gives one of the replies when every upstream replies", func(t *testing.T) {
		upstreams := []gateway.Upstream{
			quick{name: "a", reply: gateway.Reply{Content: "Hello"}},
			quick{name: "b", reply: gateway.Reply{Content: "Hello"}},
		}
		reply, err := gateway.Fanout(context.Background(), upstreams, hello)
		if err != nil || reply.Content != "Hello" || (reply.Upstream != "a" && reply.Upstream != "b") {
			t.Errorf("got %+v and the error %v, want a reply from a or b", reply, err)
		}
	})
	t.Run("tst_bwvcgs Gives an error when every upstream fails", func(t *testing.T) {
		down := &gateway.StatusError{Status: 503, Message: "down"}
		upstreams := []gateway.Upstream{quick{name: "a", err: down}, quick{name: "b", err: down}}
		if _, err := gateway.Fanout(context.Background(), upstreams, hello); !errors.Is(err, down) {
			t.Errorf("got the error %v, want the upstreams' 503", err)
		}
	})
	t.Run("tst_s0drze Gives ErrNoUpstreams for no upstreams", func(t *testing.T) {
		if _, err := gateway.Fanout(context.Background(), nil, hello); !errors.Is(err, gateway.ErrNoUpstreams) {
			t.Errorf("got the error %v, want ErrNoUpstreams", err)
		}
	})
}
