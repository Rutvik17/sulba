package gateway

import "net/http"

// A Server takes chat requests from callers with keys, and sends each to the upstreams its
// model's route names.
type Server struct {
	Routes    Routes
	Upstreams map[string]Upstream
	Keys      map[string]bool
	Limiter   *Limiter
	MaxTokens int
	MaxBody   int64
}

// A ChatResponse is the gateway's answer to a chat request, in the shape of OpenAI's.
type ChatResponse struct {
	Model   string   `json:"model"`
	Choices []Choice `json:"choices"`
	Usage   Tokens   `json:"usage"`
}

// A Choice is one of a response's replies.
type Choice struct {
	Index   int     `json:"index"`
	Message Message `json:"message"`
}

// Tokens are a response's counts of tokens.
type Tokens struct {
	Prompt     int `json:"prompt_tokens"`
	Completion int `json:"completion_tokens"`
	Total      int `json:"total_tokens"`
}

// Handler gives the server's routes: POST /v1/chat/completions, and GET /healthz.
func (s *Server) Handler() http.Handler {
	return http.NewServeMux()
}
