package tests

import (
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"example/gateway"
)

func decode(body string) (gateway.ChatRequest, error) {
	return gateway.DecodeRequest(strings.NewReader(body), 1024)
}

// fieldError gives the FieldError inside err, or fails the test.
func fieldError(t *testing.T, err error, field string) *gateway.FieldError {
	t.Helper()
	wrong, ok := errors.AsType[*gateway.FieldError](err)
	if !ok {
		t.Fatalf("got the error %v, want a *FieldError for %s", err, field)
	}
	if wrong.Field != field {
		t.Fatalf("got a FieldError for %q, want one for %q", wrong.Field, field)
	}
	return wrong
}

func TestDecodeRequest(t *testing.T) {
	t.Run("tst_k70480 Reads the model, the messages and max_tokens", func(t *testing.T) {
		request, err := decode(`{"model": "qwen", "max_tokens": 200, "stream": true,
			"messages": [{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Hi"}]}`)
		if err != nil {
			t.Fatalf("got the error %v, want none", err)
		}
		want := gateway.ChatRequest{
			Model:     "qwen",
			Messages:  []gateway.Message{{Role: "system", Content: "Be brief."}, {Role: "user", Content: "Hi"}},
			MaxTokens: 200,
			Stream:    true,
		}
		if request.Model != want.Model || request.MaxTokens != want.MaxTokens || request.Stream != want.Stream {
			t.Fatalf("got %+v, want %+v", request, want)
		}
		if len(request.Messages) != 2 || request.Messages[0] != want.Messages[0] || request.Messages[1] != want.Messages[1] {
			t.Fatalf("got the messages %+v, want %+v", request.Messages, want.Messages)
		}
	})
	t.Run("tst_5ogbdi Gives a request that asks for no max_tokens the limit", func(t *testing.T) {
		request, err := decode(`{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}]}`)
		if err != nil {
			t.Fatalf("got the error %v, want none", err)
		}
		if request.MaxTokens != 1024 {
			t.Errorf("got max_tokens %d, want the limit, 1024", request.MaxTokens)
		}
	})
	t.Run("tst_u9trg3 Refuses a body that isn't JSON as ErrNotJSON, keeping json's error", func(t *testing.T) {
		_, err := decode(`{"model": "qwen", "messages": [`)
		if !errors.Is(err, gateway.ErrNotJSON) {
			t.Fatalf("got the error %v, want one that wraps ErrNotJSON", err)
		}
		_, err = decode(`{"model": qwen}`)
		if _, ok := errors.AsType[*json.SyntaxError](err); !ok || !errors.Is(err, gateway.ErrNotJSON) {
			t.Fatalf("got the error %v, want one that wraps ErrNotJSON and json's *SyntaxError", err)
		}
		if _, err := decode(""); !errors.Is(err, gateway.ErrNotJSON) {
			t.Errorf("an empty body gave the error %v, want one that wraps ErrNotJSON", err)
		}
	})
	t.Run("tst_1fjdc4 Refuses more after the JSON object", func(t *testing.T) {
		_, err := decode(`{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}]} {"model": "other"}`)
		if !errors.Is(err, gateway.ErrNotJSON) {
			t.Errorf("got the error %v, want one that wraps ErrNotJSON", err)
		}
	})
	t.Run("tst_t1ppzh Refuses a request with no model or no messages", func(t *testing.T) {
		if _, err := decode(`{"messages": [{"role": "user", "content": "Hi"}]}`); !errors.Is(err, gateway.ErrNoModel) {
			t.Errorf("with no model, got the error %v, want ErrNoModel", err)
		}
		if _, err := decode(`{"model": "qwen", "messages": []}`); !errors.Is(err, gateway.ErrNoMessages) {
			t.Errorf("with no messages, got the error %v, want ErrNoMessages", err)
		}
		if _, err := decode(`{"model": "qwen"}`); !errors.Is(err, gateway.ErrNoMessages) {
			t.Errorf("with the messages left out, got the error %v, want ErrNoMessages", err)
		}
	})
	t.Run("tst_l1jsfs Names the message whose role is wrong", func(t *testing.T) {
		_, err := decode(`{"model": "qwen", "messages": [{"role": "user", "content": "Hi"}, {"role": "tool", "content": "{}"}]}`)
		wrong := fieldError(t, err, "messages.1.role")
		if !strings.Contains(wrong.Error(), "tool") {
			t.Errorf("got the message %q, want it to say the role it got, tool", wrong.Error())
		}
	})
	t.Run("tst_mm28le Names a field of the wrong type", func(t *testing.T) {
		_, err := decode(`{"model": "qwen", "max_tokens": "lots", "messages": [{"role": "user", "content": "Hi"}]}`)
		fieldError(t, err, "max_tokens")
		_, err = decode(`{"model": "qwen", "messages": [{"role": "user", "content": 5}]}`)
		fieldError(t, err, "messages.0.content")
	})
	t.Run("tst_f5n4vu Refuses max_tokens below zero or over the limit", func(t *testing.T) {
		_, err := decode(`{"model": "qwen", "max_tokens": -1, "messages": [{"role": "user", "content": "Hi"}]}`)
		fieldError(t, err, "max_tokens")
		_, err = decode(`{"model": "qwen", "max_tokens": 1025, "messages": [{"role": "user", "content": "Hi"}]}`)
		wrong := fieldError(t, err, "max_tokens")
		if !strings.Contains(wrong.Error(), "1024") {
			t.Errorf("got the message %q, want it to give the limit, 1024", wrong.Error())
		}
		if _, err := decode(`{"model": "qwen", "max_tokens": 1024, "messages": [{"role": "user", "content": "Hi"}]}`); err != nil {
			t.Errorf("at the limit, got the error %v, want none", err)
		}
	})
}
