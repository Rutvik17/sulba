package gateway

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// An HTTPUpstream is a model server with an API like OpenAI's, such as llama.cpp's server.
type HTTPUpstream struct {
	name    string
	baseURL string
	client  *http.Client
}

// NewHTTPUpstream gives the upstream called name, at baseURL, asked through client.
func NewHTTPUpstream(name, baseURL string, client *http.Client) *HTTPUpstream {
	return &HTTPUpstream{name: name, baseURL: strings.TrimSuffix(baseURL, "/"), client: client}
}

// Name gives the upstream's name.
func (u *HTTPUpstream) Name() string {
	return u.name
}

// The most the gateway reads of an upstream's reply, and of its error.
const (
	maxReply = 1 << 20
	maxError = 4 << 10
)

// Chat posts the request to the upstream's /v1/chat/completions and gives its reply. An answer
// that isn't a success gives a *StatusError, with what the upstream said and the wait its
// Retry-After asked for.
func (u *HTTPUpstream) Chat(ctx context.Context, request ChatRequest) (Reply, error) {
	body, err := json.Marshal(request)
	if err != nil {
		return Reply{}, err
	}
	post, err := http.NewRequestWithContext(ctx, http.MethodPost, u.baseURL+"/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return Reply{}, err
	}
	post.Header.Set("Content-Type", "application/json")
	response, err := u.client.Do(post)
	if err != nil {
		return Reply{}, err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return Reply{}, statusError(response)
	}
	var answer ChatResponse
	if err := json.NewDecoder(io.LimitReader(response.Body, maxReply)).Decode(&answer); err != nil {
		return Reply{}, fmt.Errorf("reading %s's reply: %w", u.name, err)
	}
	if len(answer.Choices) == 0 {
		return Reply{}, fmt.Errorf("%s's reply has no choices", u.name)
	}
	return Reply{
		Content:      answer.Choices[0].Message.Content,
		PromptTokens: answer.Usage.Prompt,
		ReplyTokens:  answer.Usage.Completion,
	}, nil
}

// statusError gives an answer that isn't a success as a *StatusError: its status, its message,
// from an error body like the gateway's own or its text, and the seconds of its Retry-After.
func statusError(response *http.Response) error {
	said, _ := io.ReadAll(io.LimitReader(response.Body, maxError))
	status := &StatusError{Status: response.StatusCode, Message: strings.TrimSpace(string(said))}
	var body ErrorBody
	if json.Unmarshal(said, &body) == nil && body.Error.Message != "" {
		status.Message = body.Error.Message
	}
	if seconds, err := strconv.Atoi(response.Header.Get("Retry-After")); err == nil && seconds > 0 {
		status.RetryAfter = time.Duration(seconds) * time.Second
	}
	return status
}
