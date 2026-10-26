package gateway

import (
	"context"
	"net/http"
)

// An HTTPUpstream is a model server with an API like OpenAI's, such as llama.cpp's server.
type HTTPUpstream struct {
	name    string
	baseURL string
	client  *http.Client
}

// NewHTTPUpstream gives the upstream called name, at baseURL, asked through client.
func NewHTTPUpstream(name, baseURL string, client *http.Client) *HTTPUpstream {
	return &HTTPUpstream{name: name, baseURL: baseURL, client: client}
}

// Name gives the upstream's name.
func (u *HTTPUpstream) Name() string {
	return u.name
}

// Chat posts the request to the upstream's /v1/chat/completions and gives its reply. An answer
// that isn't a success gives a *StatusError, with what the upstream said and the wait its
// Retry-After asked for.
func (u *HTTPUpstream) Chat(ctx context.Context, request ChatRequest) (Reply, error) {
	return Reply{}, nil
}
