package gateway

import (
	"context"
	"sync"
)

// A Gate lets at most a set number of calls through at once.
type Gate struct {
	slots chan struct{}
}

// NewGate gives a gate that lets n calls through at once.
func NewGate(n int) *Gate {
	return &Gate{slots: make(chan struct{}, n)}
}

// Do runs call once the gate has room for it, and gives its error. If ctx is done before there's
// room, it gives ctx's error without running call.
func (g *Gate) Do(ctx context.Context, call func(context.Context) error) error {
	select {
	case g.slots <- struct{}{}:
	case <-ctx.Done():
		return ctx.Err()
	}
	defer func() { <-g.slots }()
	return call(ctx)
}

// InFlight gives how many calls are through the gate now.
func (g *Gate) InFlight() int {
	return len(g.slots)
}

// ChatAll sends the requests to upstream all at once, through gate, and gives the replies in the
// requests' order. The first error cancels the requests still running, and once every one has
// stopped, ChatAll gives that error.
func ChatAll(ctx context.Context, gate *Gate, upstream Upstream, requests []ChatRequest) ([]Reply, error) {
	ctx, cancel := context.WithCancelCause(ctx)
	defer cancel(nil)
	replies := make([]Reply, len(requests))
	var group sync.WaitGroup
	for i, request := range requests {
		group.Go(func() {
			err := gate.Do(ctx, func(ctx context.Context) error {
				reply, err := upstream.Chat(ctx, request)
				replies[i] = reply
				return err
			})
			if err != nil {
				cancel(err)
			}
		})
	}
	group.Wait()
	if err := context.Cause(ctx); err != nil {
		return nil, err
	}
	return replies, nil
}
