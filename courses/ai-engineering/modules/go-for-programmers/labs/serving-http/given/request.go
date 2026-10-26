package gateway

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
)

// A Message is one turn of a chat: who said it, and what they said.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// A ChatRequest is what a caller asks the gateway for.
type ChatRequest struct {
	Model     string    `json:"model"`
	Messages  []Message `json:"messages"`
	MaxTokens int       `json:"max_tokens,omitempty"`
	Stream    bool      `json:"stream,omitempty"`
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

var roles = map[string]bool{"system": true, "user": true, "assistant": true}

// DecodeRequest reads a chat request from r and checks it. A request that asks for no
// max_tokens gets limit, and one may ask for no more than limit.
func DecodeRequest(r io.Reader, limit int) (ChatRequest, error) {
	decoder := json.NewDecoder(r)
	var request ChatRequest
	if err := decoder.Decode(&request); err != nil {
		if wrongType, ok := errors.AsType[*json.UnmarshalTypeError](err); ok && wrongType.Field != "" {
			return ChatRequest{}, &FieldError{Field: wrongType.Field, Problem: "can't be a " + wrongType.Value}
		}
		return ChatRequest{}, fmt.Errorf("%w: %w", ErrNotJSON, err)
	}
	if decoder.More() {
		return ChatRequest{}, fmt.Errorf("%w: there's more after it", ErrNotJSON)
	}
	if request.Model == "" {
		return ChatRequest{}, ErrNoModel
	}
	if len(request.Messages) == 0 {
		return ChatRequest{}, ErrNoMessages
	}
	for i, message := range request.Messages {
		if !roles[message.Role] {
			field := fmt.Sprintf("messages.%d.role", i)
			return ChatRequest{}, &FieldError{Field: field, Problem: fmt.Sprintf("can't be %q", message.Role)}
		}
	}
	switch {
	case request.MaxTokens < 0:
		return ChatRequest{}, &FieldError{Field: "max_tokens", Problem: "can't be negative"}
	case request.MaxTokens > limit:
		return ChatRequest{}, &FieldError{Field: "max_tokens", Problem: fmt.Sprintf("can't be more than %d", limit)}
	case request.MaxTokens == 0:
		request.MaxTokens = limit
	}
	return request, nil
}
