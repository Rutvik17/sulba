package gateway

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
)

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
	mux := http.NewServeMux()
	mux.HandleFunc("POST /v1/chat/completions", s.chat)
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "ok")
	})
	return mux
}

func (s *Server) chat(w http.ResponseWriter, r *http.Request) {
	key, found := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
	if !found || !s.Keys[key] {
		w.Header().Set("WWW-Authenticate", `Bearer realm="gateway"`)
		refuse(w, http.StatusUnauthorized, "unauthorized", "Send a key the gateway knows, as Authorization: Bearer KEY.")
		return
	}
	if s.Limiter != nil && !s.Limiter.For(key).Allow() {
		w.Header().Set("Retry-After", "1")
		refuse(w, http.StatusTooManyRequests, "rate_limited", "This key is over its rate limit.")
		return
	}
	request, err := DecodeRequest(http.MaxBytesReader(w, r.Body, s.MaxBody), s.MaxTokens)
	if _, tooBig := errors.AsType[*http.MaxBytesError](err); tooBig {
		refuse(w, http.StatusRequestEntityTooLarge, "too_large", fmt.Sprintf("The request is over %d bytes.", s.MaxBody))
		return
	}
	if err != nil {
		WriteError(w, err)
		return
	}
	names, err := s.Routes.For(request.Model)
	if err != nil {
		WriteError(w, err)
		return
	}
	upstreams := make([]Upstream, 0, len(names))
	for _, name := range names {
		upstream, found := s.Upstreams[name]
		if !found {
			WriteError(w, fmt.Errorf("the route for %s names %s, which the server doesn't have", request.Model, name))
			return
		}
		upstreams = append(upstreams, upstream)
	}
	reply, err := Fallback(r.Context(), upstreams, request)
	if err != nil {
		WriteError(w, err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Upstream", reply.Upstream)
	json.NewEncoder(w).Encode(ChatResponse{
		Model:   request.Model,
		Choices: []Choice{{Message: Message{Role: "assistant", Content: reply.Content}}},
		Usage: Tokens{
			Prompt:     reply.PromptTokens,
			Completion: reply.ReplyTokens,
			Total:      reply.PromptTokens + reply.ReplyTokens,
		},
	})
}

// refuse answers with the gateway's own error, for what its other errors don't cover.
func refuse(w http.ResponseWriter, status int, kind, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(ErrorBody{Error: ErrorDetail{Type: kind, Message: message}})
}
