package tests

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http/httptest"
	"testing"
	"time"

	"example/gateway"
)

// answer gives the gateway's answer to err: its status, its body and the recorder.
func answer(t *testing.T, err error) (int, gateway.ErrorDetail, *httptest.ResponseRecorder) {
	t.Helper()
	recorder := httptest.NewRecorder()
	gateway.WriteError(recorder, err)
	var body gateway.ErrorBody
	if decoded := json.Unmarshal(recorder.Body.Bytes(), &body); decoded != nil {
		t.Fatalf("for %v, got the body %q, which isn't an ErrorBody: %v", err, recorder.Body.String(), decoded)
	}
	return recorder.Code, body.Error, recorder
}

func expect(t *testing.T, err error, status int, kind string) gateway.ErrorDetail {
	t.Helper()
	got, detail, _ := answer(t, err)
	if got != status || detail.Type != kind {
		t.Errorf("for %v, got %d %q, want %d %q", err, got, detail.Type, status, kind)
	}
	return detail
}

func upstream(name string, code int, said string, wait time.Duration) error {
	return fmt.Errorf("upstream %s: %w", name, &gateway.StatusError{Status: code, Message: said, RetryAfter: wait})
}

func TestWriteError(t *testing.T) {
	t.Run("tst_anw65b Answers a request the gateway can't read with 400", func(t *testing.T) {
		for _, err := range []error{
			fmt.Errorf("%w: unexpected EOF", gateway.ErrNotJSON),
			gateway.ErrNoModel,
			gateway.ErrNoMessages,
			&gateway.FieldError{Field: "max_tokens", Problem: "can't be negative"},
		} {
			detail := expect(t, err, 400, "invalid_request")
			if detail.Message != err.Error() {
				t.Errorf("for %v, got the message %q, want the error's own", err, detail.Message)
			}
		}
	})
	t.Run("tst_i53u2o Answers an unknown model with 404", func(t *testing.T) {
		err := fmt.Errorf("%w %q", gateway.ErrUnknownModel, "gpt-9")
		detail := expect(t, err, 404, "unknown_model")
		if detail.Message != err.Error() {
			t.Errorf("got the message %q, want the error's own", detail.Message)
		}
	})
	t.Run("tst_x44m2e Answers in JSON", func(t *testing.T) {
		_, _, recorder := answer(t, gateway.ErrNoModel)
		if got := recorder.Header().Get("Content-Type"); got != "application/json" {
			t.Errorf("got the Content-Type %q, want application/json", got)
		}
	})
	t.Run("tst_hprwoh Answers with 429 when every upstream is busy", func(t *testing.T) {
		err := errors.Join(upstream("a", 429, "slow down", 0), upstream("b", 429, "slow down", 0))
		detail := expect(t, err, 429, "rate_limited")
		if detail.Message != "Every upstream is busy. Try again later." {
			t.Errorf("got the message %q", detail.Message)
		}
	})
	t.Run("tst_x0tx8w Answers with 502 when the upstreams fail", func(t *testing.T) {
		err := errors.Join(upstream("a", 503, "down", 0), upstream("b", 500, "broken", 0))
		detail := expect(t, err, 502, "upstream_error")
		if detail.Message != "No upstream could answer." {
			t.Errorf("got the message %q", detail.Message)
		}
	})
	t.Run("tst_tsyp7r Answers a deadline with 504", func(t *testing.T) {
		err := errors.Join(upstream("a", 503, "down", 0), context.DeadlineExceeded)
		detail := expect(t, err, 504, "timeout")
		if detail.Message != "No upstream answered in time." {
			t.Errorf("got the message %q", detail.Message)
		}
	})
	t.Run("tst_18d3v1 Answers anything else with 500, in its own words", func(t *testing.T) {
		err := errors.New("open /etc/gateway/keys.json: permission denied")
		detail := expect(t, err, 500, "internal")
		if detail.Message != "The gateway failed." {
			t.Errorf("got the message %q", detail.Message)
		}
	})
}
