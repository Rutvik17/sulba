package gateway

import (
	"context"
	"errors"
)

type answer struct {
	reply Reply
	err   error
}

// Fanout asks every upstream at once, gives the first reply, and cancels the rest. When none
// replies, it gives their errors joined, and once ctx is done, ctx's error.
func Fanout(ctx context.Context, upstreams []Upstream, request ChatRequest) (Reply, error) {
	if len(upstreams) == 0 {
		return Reply{}, ErrNoUpstreams
	}
	asking, cancel := context.WithCancel(ctx)
	defer cancel()
	answers := make(chan answer)
	for _, upstream := range upstreams {
		go func() {
			reply, err := upstream.Chat(ctx, request)
			if err == nil {
				reply.Upstream = upstream.Name()
			}
			answers <- answer{reply, err}
		}()
	}
	return firstReply(asking, answers, len(upstreams))
}

// firstReply gives the first of n answers that's a reply, or every answer's error, joined.
func firstReply(ctx context.Context, answers <-chan answer, n int) (Reply, error) {
	var failures []error
	for range n {
		got := <-answers
		if got.err != nil {
			failures = append(failures, got.err)
			return Reply{}, errors.Join(failures...)
		}
		return got.reply, nil
	}
	return Reply{}, errors.Join(failures...)
}
