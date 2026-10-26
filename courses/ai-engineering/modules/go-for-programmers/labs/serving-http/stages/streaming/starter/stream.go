package gateway

import (
	"context"
	"net/http"
)

// A Chunk is one event of a streamed reply, in the shape of OpenAI's.
type Chunk struct {
	Object  string        `json:"object"`
	Model   string        `json:"model"`
	Choices []ChunkChoice `json:"choices"`
}

// A ChunkChoice is a chunk's piece of a reply.
type ChunkChoice struct {
	Index int   `json:"index"`
	Delta Delta `json:"delta"`
}

// A Delta is the text a chunk adds.
type Delta struct {
	Content string `json:"content"`
}

// Stream asks the upstream for its reply as server-sent events, and calls each with each piece of
// the reply's text as it arrives. It stops at the first error each gives, and gives that. Once
// the stream ends, it gives the reply, with the whole text.
func (u *HTTPUpstream) Stream(ctx context.Context, request ChatRequest, each func(piece string) error) (Reply, error) {
	return Reply{}, nil
}

// Relay answers a request that asked to stream with the upstream's reply as server-sent events,
// as OpenAI's API sends them: a chunk for each piece, flushed as it's written, then
// data: [DONE]. A failure before the first piece is answered as an error. A failure after it
// ends the stream without [DONE].
func Relay(w http.ResponseWriter, r *http.Request, upstream *HTTPUpstream, request ChatRequest) error {
	return nil
}
