package gateway

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"
)

// A Reply is an upstream's answer to a chat request.
type Reply struct {
	Upstream     string
	Content      string
	PromptTokens int
	ReplyTokens  int
}

// An Upstream is a model server the gateway can ask.
type Upstream interface {
	Name() string
	Chat(ctx context.Context, request ChatRequest) (Reply, error)
}

// A StatusError is an upstream's answer that wasn't a reply: its HTTP status, what it said, and
// how long it asked callers to wait, if it said.
type StatusError struct {
	Status     int
	Message    string
	RetryAfter time.Duration
}

func (e *StatusError) Error() string {
	return fmt.Sprintf("%d %s: %s", e.Status, http.StatusText(e.Status), e.Message)
}

var ErrNoUpstreams = errors.New("no upstreams to ask")

// Retryable reports whether another upstream might answer where err came from: one that was busy
// (429) or failing (5xx), or one that ran out of time.
func Retryable(err error) bool {
	if status, ok := errors.AsType[*StatusError](err); ok {
		return status.Status == http.StatusTooManyRequests || status.Status >= 500
	}
	return errors.Is(err, context.DeadlineExceeded)
}

// Fallback asks each upstream in turn and gives the first reply, with the name of the upstream
// that gave it. It stops at an error another upstream wouldn't fix, and once ctx is done. Each
// error names the upstream it came from.
func Fallback(ctx context.Context, upstreams []Upstream, request ChatRequest) (Reply, error) {
	if len(upstreams) == 0 {
		return Reply{}, ErrNoUpstreams
	}
	var failures []error
	for _, upstream := range upstreams {
		if err := ctx.Err(); err != nil {
			return Reply{}, errors.Join(append(failures, err)...)
		}
		reply, err := upstream.Chat(ctx, request)
		if err == nil {
			reply.Upstream = upstream.Name()
			return reply, nil
		}
		err = fmt.Errorf("upstream %s: %w", upstream.Name(), err)
		if !Retryable(err) {
			return Reply{}, err
		}
		failures = append(failures, err)
	}
	return Reply{}, errors.Join(failures...)
}
