package gateway

import (
	"errors"
	"io"
)

// A Message is one turn of a chat: who said it, and what they said.
type Message struct {
	Role    string
	Content string
}

// A ChatRequest is what a caller asks the gateway for. In JSON its fields are model, messages,
// max_tokens and stream.
type ChatRequest struct {
	Model     string
	Messages  []Message
	MaxTokens int
	Stream    bool
}

var (
	ErrNotJSON    = errors.New("the request isn't one JSON object")
	ErrNoModel    = errors.New("the request names no model")
	ErrNoMessages = errors.New("the request has no messages")
)

// A FieldError says which field of a request is wrong, and how.
type FieldError struct {
	Field   string
	Problem string
}

func (e *FieldError) Error() string {
	return e.Field + " " + e.Problem
}

// DecodeRequest reads a chat request from r and checks it. A request that asks for no
// max_tokens gets limit, and one may ask for no more than limit.
func DecodeRequest(r io.Reader, limit int) (ChatRequest, error) {
	return ChatRequest{}, nil
}
