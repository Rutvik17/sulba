package checks

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"example/gateway"
)

func answer(err error) (*httptest.ResponseRecorder, gateway.ErrorDetail) {
	recorder := httptest.NewRecorder()
	gateway.WriteError(recorder, err)
	var body gateway.ErrorBody
	json.Unmarshal(recorder.Body.Bytes(), &body)
	return recorder, body.Error
}

func upstream(name string, code int, said string, wait time.Duration) error {
	return fmt.Errorf("upstream %s: %w", name, &gateway.StatusError{Status: code, Message: said, RetryAfter: wait})
}

const secret = "key sk-live-4f9a refused by 10.0.3.7"

func TestFailuresBeforeShipping(t *testing.T) {
	t.Run("tst_5puyzg Keeps an upstream's words inside", func(t *testing.T) {
		for _, err := range []error{
			upstream("a", 500, secret, 0),
			errors.Join(upstream("a", 429, secret, time.Second), upstream("b", 429, secret, 0)),
			upstream("a", 400, secret, 0),
		} {
			recorder, _ := answer(err)
			if body := recorder.Body.String(); strings.Contains(body, "sk-live") || strings.Contains(body, "10.0.3.7") {
				t.Errorf("for %v, the answer %q gave away what the upstream said", err, body)
			}
		}
	})
	t.Run("tst_ly8p3s Asks for the soonest wait any upstream gave", func(t *testing.T) {
		err := errors.Join(
			upstream("a", 429, "busy", 7200*time.Millisecond),
			fmt.Errorf("asking again: %w", upstream("b", 429, "busy", 3100*time.Millisecond)),
			upstream("c", 429, "busy", 0),
		)
		recorder, _ := answer(err)
		if got := recorder.Header().Get("Retry-After"); got != "4" {
			t.Errorf("got Retry-After %q, want 4, b's 3.1 seconds rounded up", got)
		}
		recorder, _ = answer(upstream("a", 429, "busy", 0))
		if got := recorder.Header().Get("Retry-After"); got != "" {
			t.Errorf("when no upstream said how long, got Retry-After %q, want none", got)
		}
	})
	t.Run("tst_osaqgr Finds an error however it's wrapped", func(t *testing.T) {
		field := &gateway.FieldError{Field: "messages.0.role", Problem: `can't be "tool"`}
		for err, want := range map[error]int{
			fmt.Errorf("handling: %w", fmt.Errorf("decoding: %w", field)):                                         400,
			errors.Join(errors.New("logged"), fmt.Errorf("route: %w", gateway.ErrUnknownModel)):                   404,
			fmt.Errorf("fallback: %w", errors.Join(upstream("a", 503, "down", 0), upstream("b", 429, "busy", 0))): 502,
		} {
			if recorder, _ := answer(err); recorder.Code != want {
				t.Errorf("for %v, got %d, want %d", err, recorder.Code, want)
			}
		}
	})
	t.Run("tst_6byhx9 Says busy only when every upstream is", func(t *testing.T) {
		recorder, detail := answer(errors.Join(upstream("a", 429, "busy", time.Second), upstream("b", 503, "down", 0)))
		if recorder.Code != 502 || detail.Type != "upstream_error" {
			t.Errorf("with one busy and one down, got %d %q, want 502 upstream_error", recorder.Code, detail.Type)
		}
		if got := recorder.Header().Get("Retry-After"); got != "" {
			t.Errorf("got Retry-After %q, want none, as b is down rather than busy", got)
		}
	})
}
