package gateway

import "context"

// A Gate lets at most a set number of calls through at once.
type Gate struct {
}

// NewGate gives a gate that lets n calls through at once.
func NewGate(n int) *Gate {
	return &Gate{}
}

// Do runs call once the gate has room for it, and gives its error. If ctx is done before there's
// room, it gives ctx's error without running call.
func (g *Gate) Do(ctx context.Context, call func(context.Context) error) error {
	return call(ctx)
}

// InFlight gives how many calls are through the gate now.
func (g *Gate) InFlight() int {
	return 0
}

// ChatAll sends the requests to upstream all at once, through gate, and gives the replies in the
// requests' order. The first error cancels the requests still running, and once every one has
// stopped, ChatAll gives that error.
func ChatAll(ctx context.Context, gate *Gate, upstream Upstream, requests []ChatRequest) ([]Reply, error) {
	return nil, nil
}
