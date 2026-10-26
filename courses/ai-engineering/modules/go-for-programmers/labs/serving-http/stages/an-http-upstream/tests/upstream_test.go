package tests

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"example/gateway"
)

var question = gateway.ChatRequest{
	Model:     "qwen",
	Messages:  []gateway.Message{{Role: "user", Content: "When do you open?"}},
	MaxTokens: 64,
}

const answer = `{"model": "qwen", "choices": [{"index": 0, "message": {"role": "assistant", "content": "At 9."}}],
	"usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}}`

// serve starts a model server that answers with handler, and gives an upstream that asks it.
func serve(t *testing.T, handler http.HandlerFunc) *gateway.HTTPUpstream {
	t.Helper()
	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)
	return gateway.NewHTTPUpstream("local", server.URL, server.Client())
}

// A counted body counts its closes.
type counted struct {
	io.ReadCloser
	closes *atomic.Int64
}

func (c counted) Close() error {
	c.closes.Add(1)
	return c.ReadCloser.Close()
}

// A counting transport gives every answer a body that counts its closes.
type counting struct {
	closes atomic.Int64
}

func (c *counting) RoundTrip(request *http.Request) (*http.Response, error) {
	response, err := http.DefaultTransport.RoundTrip(request)
	if err == nil {
		response.Body = counted{response.Body, &c.closes}
	}
	return response, err
}

func TestHTTPUpstream(t *testing.T) {
	t.Run("tst_stkegk Posts the request as JSON to /v1/chat/completions", func(t *testing.T) {
		var method, path, kind string
		var sent gateway.ChatRequest
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			method, path, kind = r.Method, r.URL.Path, r.Header.Get("Content-Type")
			json.NewDecoder(r.Body).Decode(&sent)
			io.WriteString(w, answer)
		}))
		t.Cleanup(server.Close)
		for _, base := range []string{server.URL, server.URL + "/"} {
			sent = gateway.ChatRequest{}
			gateway.NewHTTPUpstream("local", base, server.Client()).Chat(context.Background(), question)
			if method != "POST" || path != "/v1/chat/completions" || kind != "application/json" {
				t.Errorf("at %s, got %s %s with the Content-Type %q, want a POST of application/json to /v1/chat/completions", base, method, path, kind)
			}
			if sent.Model != "qwen" || sent.MaxTokens != 64 || len(sent.Messages) != 1 || sent.Messages[0].Content != "When do you open?" {
				t.Errorf("at %s, the upstream got %+v, want the request", base, sent)
			}
		}
	})
	t.Run("tst_db9zjq Gives the reply's text and tokens", func(t *testing.T) {
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, answer) })
		reply, err := upstream.Chat(context.Background(), question)
		if err != nil || reply.Content != "At 9." || reply.PromptTokens != 12 || reply.ReplyTokens != 4 {
			t.Errorf("got %+v and the error %v, want At 9., with 12 and 4 tokens", reply, err)
		}
	})
	t.Run("tst_945h26 Gives a StatusError with what the upstream said", func(t *testing.T) {
		json := true
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) {
			if !json {
				http.Error(w, "upstream crashed", 500)
				return
			}
			w.WriteHeader(503)
			io.WriteString(w, `{"error": {"code": 503, "message": "Loading model", "type": "unavailable_error"}}`)
		})
		_, err := upstream.Chat(context.Background(), question)
		if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.Status != 503 || status.Message != "Loading model" {
			t.Errorf("got the error %v, want a StatusError of 503 with the message Loading model", err)
		}
		json = false
		_, err = upstream.Chat(context.Background(), question)
		if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.Status != 500 || status.Message != "upstream crashed" {
			t.Errorf("for an error in text, got %v, want a StatusError of 500 with the message upstream crashed", err)
		}
	})
	t.Run("tst_e0qmsb Reads Retry-After as the wait", func(t *testing.T) {
		wait := "2"
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) {
			if wait != "" {
				w.Header().Set("Retry-After", wait)
			}
			w.WriteHeader(429)
			io.WriteString(w, `{"error": {"message": "busy"}}`)
		})
		_, err := upstream.Chat(context.Background(), question)
		if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.RetryAfter != 2*time.Second {
			t.Errorf("got the error %v, want a StatusError that asks for 2s", err)
		}
		wait = ""
		_, err = upstream.Chat(context.Background(), question)
		if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.RetryAfter != 0 {
			t.Errorf("with no Retry-After, got the error %v, want a StatusError that asks for no wait", err)
		}
	})
	t.Run("tst_e6bxrj Stops when the caller is done", func(t *testing.T) {
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) {
			// The server sees its caller hang up once it has read the request.
			io.Copy(io.Discard, r.Body)
			select {
			case <-r.Context().Done():
			case <-time.After(10 * time.Second):
			}
		})
		ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
		defer cancel()
		start := time.Now()
		_, err := upstream.Chat(ctx, question)
		if !errors.Is(err, context.DeadlineExceeded) || time.Since(start) > 2*time.Second {
			t.Errorf("got the error %v after %v, want DeadlineExceeded at the 100ms deadline", err, time.Since(start).Round(time.Millisecond))
		}
	})
	t.Run("tst_73054t Closes the body of every answer", func(t *testing.T) {
		calls := 0
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			calls++
			switch calls {
			case 1:
				io.WriteString(w, answer)
			case 2:
				http.Error(w, "down", 503)
			default:
				io.WriteString(w, "not JSON")
			}
		}))
		defer server.Close()
		transport := &counting{}
		upstream := gateway.NewHTTPUpstream("local", server.URL, &http.Client{Transport: transport})
		for range 3 {
			upstream.Chat(context.Background(), question)
		}
		if got := transport.closes.Load(); got != 3 {
			t.Errorf("closed %d of 3 answers' bodies, want all 3", got)
		}
	})
	t.Run("tst_1qmxh3 Gives an error for a reply that isn't JSON, or has no choices", func(t *testing.T) {
		body := "not JSON"
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, body) })
		if _, err := upstream.Chat(context.Background(), question); err == nil {
			t.Errorf("for a reply that isn't JSON, got no error")
		}
		body = `{"choices": []}`
		if _, err := upstream.Chat(context.Background(), question); err == nil {
			t.Errorf("for a reply with no choices, got no error")
		}
	})
	t.Run("tst_m30s9c Reads no more than a megabyte of a reply", func(t *testing.T) {
		upstream := serve(t, func(w http.ResponseWriter, r *http.Request) {
			io.WriteString(w, `{"choices": [{"message": {"role": "assistant", "content": "`)
			io.WriteString(w, strings.Repeat("a", 2<<20))
			io.WriteString(w, `"}}]}`)
		})
		if reply, err := upstream.Chat(context.Background(), question); err == nil {
			t.Errorf("read a reply of %d bytes, want an error past a megabyte", len(reply.Content))
		}
	})
}
