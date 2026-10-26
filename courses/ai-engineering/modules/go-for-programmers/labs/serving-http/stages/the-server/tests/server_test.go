package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"example/gateway"
)

// A fake upstream gives its reply or its error, and keeps the context of its last call.
type fake struct {
	name  string
	reply gateway.Reply
	err   error
	ctx   context.Context
}

func (f *fake) Name() string {
	return f.name
}

func (f *fake) Chat(ctx context.Context, request gateway.ChatRequest) (gateway.Reply, error) {
	f.ctx = ctx
	return f.reply, f.err
}

func server(upstreams ...*fake) *gateway.Server {
	routes := gateway.Routes{"qwen": nil}
	byName := map[string]gateway.Upstream{}
	for _, each := range upstreams {
		routes["qwen"] = append(routes["qwen"], each.name)
		byName[each.name] = each
	}
	return &gateway.Server{
		Routes:    routes,
		Upstreams: byName,
		Keys:      map[string]bool{"key-a": true},
		MaxTokens: 1024,
		MaxBody:   4096,
	}
}

const hello = `{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}]}`

// ask sends a chat request to the server's handler, with key unless it's empty.
func ask(s *gateway.Server, key, body string) *httptest.ResponseRecorder {
	request := httptest.NewRequest("POST", "/v1/chat/completions", strings.NewReader(body))
	if key != "" {
		request.Header.Set("Authorization", "Bearer "+key)
	}
	recorder := httptest.NewRecorder()
	s.Handler().ServeHTTP(recorder, request)
	return recorder
}

func errorType(t *testing.T, recorder *httptest.ResponseRecorder) string {
	t.Helper()
	var body gateway.ErrorBody
	if err := json.Unmarshal(recorder.Body.Bytes(), &body); err != nil {
		t.Fatalf("got the body %q, which isn't an ErrorBody", recorder.Body.String())
	}
	return body.Error.Type
}

func TestServer(t *testing.T) {
	t.Run("tst_yzhr1f Answers with the upstream's reply, in OpenAI's shape", func(t *testing.T) {
		a := &fake{name: "a", reply: gateway.Reply{Content: "Hello", PromptTokens: 9, ReplyTokens: 2}}
		recorder := ask(server(a), "key-a", hello)
		var response gateway.ChatResponse
		if err := json.Unmarshal(recorder.Body.Bytes(), &response); err != nil || recorder.Code != 200 {
			t.Fatalf("got %d %q, want 200 and a ChatResponse", recorder.Code, recorder.Body.String())
		}
		if len(response.Choices) != 1 || response.Choices[0].Message != (gateway.Message{Role: "assistant", Content: "Hello"}) {
			t.Errorf("got the choices %+v, want one assistant message, Hello", response.Choices)
		}
		if response.Model != "qwen" || response.Usage != (gateway.Tokens{Prompt: 9, Completion: 2, Total: 11}) {
			t.Errorf("got the model %q and usage %+v, want qwen and 9, 2 and 11 tokens", response.Model, response.Usage)
		}
		if got := recorder.Header().Get("Content-Type"); got != "application/json" {
			t.Errorf("got the Content-Type %q, want application/json", got)
		}
	})
	t.Run("tst_70htuu Refuses a request without a key it knows, with 401 and a Bearer challenge", func(t *testing.T) {
		a := &fake{name: "a", reply: gateway.Reply{Content: "Hello"}}
		for _, key := range []string{"", "key-b"} {
			if recorder := ask(server(a), key, hello); recorder.Code != 401 || errorType(t, recorder) != "unauthorized" {
				t.Errorf("with the key %q, got %d %q, want 401 unauthorized", key, recorder.Code, recorder.Body.String())
			} else if challenge := recorder.Header().Get("WWW-Authenticate"); challenge != `Bearer realm="gateway"` {
				t.Errorf("with the key %q, got the WWW-Authenticate %q, want Bearer realm=\"gateway\"", key, challenge)
			}
		}
		request := httptest.NewRequest("POST", "/v1/chat/completions", strings.NewReader(hello))
		request.Header.Set("Authorization", "Basic key-a")
		recorder := httptest.NewRecorder()
		server(a).Handler().ServeHTTP(recorder, request)
		if recorder.Code != 401 {
			t.Errorf("with the key sent as Basic, got %d, want 401", recorder.Code)
		}
		if a.ctx != nil {
			t.Errorf("asked the upstream for a request without a key")
		}
	})
	t.Run("tst_iqcmkb Refuses a key over its rate limit, with 429 and Retry-After", func(t *testing.T) {
		s := server(&fake{name: "a", reply: gateway.Reply{Content: "Hello"}})
		s.Limiter = gateway.NewLimiter(0.001, 2)
		ask(s, "key-a", hello)
		ask(s, "key-a", hello)
		recorder := ask(s, "key-a", hello)
		if recorder.Code != 429 || errorType(t, recorder) != "rate_limited" || recorder.Header().Get("Retry-After") == "" {
			t.Errorf("for a third request with a burst of 2, got %d %q, want 429 rate_limited with Retry-After", recorder.Code, recorder.Body.String())
		}
	})
	t.Run("tst_iq52pr Refuses a body over MaxBody, with 413", func(t *testing.T) {
		s := server(&fake{name: "a", reply: gateway.Reply{Content: "Hello"}})
		big := `{"model": "qwen", "messages": [{"role": "user", "content": "` + strings.Repeat("a", 5000) + `"}]}`
		if recorder := ask(s, "key-a", big); recorder.Code != 413 || errorType(t, recorder) != "too_large" {
			t.Errorf("got %d %q, want 413 too_large", recorder.Code, recorder.Body.String())
		}
	})
	t.Run("tst_wflv5i Answers what it can't read with 400, and an unknown model with 404", func(t *testing.T) {
		s := server(&fake{name: "a", reply: gateway.Reply{Content: "Hello"}})
		if recorder := ask(s, "key-a", `{"model": "qwen"`); recorder.Code != 400 {
			t.Errorf("for a body cut short, got %d, want 400", recorder.Code)
		}
		if recorder := ask(s, "key-a", `{"model": "gpt-9", "messages": [{"role": "user", "content": "Hi"}]}`); recorder.Code != 404 {
			t.Errorf("for an unknown model, got %d, want 404", recorder.Code)
		}
	})
	t.Run("tst_z8lw00 Falls back along the model's route, and names the upstream that answered", func(t *testing.T) {
		a := &fake{name: "a", err: &gateway.StatusError{Status: 503, Message: "down"}}
		b := &fake{name: "b", reply: gateway.Reply{Content: "Hello"}}
		recorder := ask(server(a, b), "key-a", hello)
		if recorder.Code != 200 || recorder.Header().Get("X-Upstream") != "b" {
			t.Errorf("got %d with X-Upstream %q, want 200 from b", recorder.Code, recorder.Header().Get("X-Upstream"))
		}
	})
	t.Run("tst_ersdu8 Answers 405 to a GET of chat completions, and ok on /healthz", func(t *testing.T) {
		handler := server(&fake{name: "a"}).Handler()
		recorder := httptest.NewRecorder()
		handler.ServeHTTP(recorder, httptest.NewRequest("GET", "/v1/chat/completions", nil))
		if recorder.Code != http.StatusMethodNotAllowed {
			t.Errorf("for a GET of chat completions, got %d, want 405", recorder.Code)
		}
		recorder = httptest.NewRecorder()
		handler.ServeHTTP(recorder, httptest.NewRequest("GET", "/healthz", nil))
		if recorder.Code != 200 || strings.TrimSpace(recorder.Body.String()) != "ok" {
			t.Errorf("for /healthz, got %d %q, want 200 ok", recorder.Code, recorder.Body.String())
		}
	})
	t.Run("tst_53fyl8 Passes the caller's context to the upstreams", func(t *testing.T) {
		a := &fake{name: "a", reply: gateway.Reply{Content: "Hello"}}
		ctx, cancel := context.WithCancel(context.Background())
		request := httptest.NewRequestWithContext(ctx, "POST", "/v1/chat/completions", strings.NewReader(hello))
		request.Header.Set("Authorization", "Bearer key-a")
		server(a).Handler().ServeHTTP(httptest.NewRecorder(), request)
		cancel()
		if a.ctx == nil || a.ctx.Err() == nil {
			t.Errorf("the upstream's context wasn't the caller's: canceling the caller's didn't cancel it")
		}
	})
}
