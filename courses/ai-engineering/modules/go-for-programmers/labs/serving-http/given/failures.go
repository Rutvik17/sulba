package gateway

import (
	"context"
	"encoding/json"
	"errors"
	"math"
	"net/http"
	"strconv"
	"time"
)

// An ErrorBody is the JSON the gateway answers a failed request with.
type ErrorBody struct {
	Error ErrorDetail `json:"error"`
}

// An ErrorDetail says what kind of failure it was, and what went wrong.
type ErrorDetail struct {
	Type    string `json:"type"`
	Message string `json:"message"`
}

// WriteError answers a request that failed with err.
func WriteError(w http.ResponseWriter, err error) {
	status, detail, wait := describe(err)
	if wait > 0 {
		w.Header().Set("Retry-After", strconv.Itoa(int(math.Ceil(wait.Seconds()))))
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(ErrorBody{Error: detail})
}

// describe gives the status, the detail and the wait to answer err with. Only the gateway's own
// errors give their words to the caller: an upstream's could say anything about it.
func describe(err error) (int, ErrorDetail, time.Duration) {
	_, wrongField := errors.AsType[*FieldError](err)
	switch {
	case wrongField, errors.Is(err, ErrNotJSON), errors.Is(err, ErrNoModel), errors.Is(err, ErrNoMessages):
		return http.StatusBadRequest, ErrorDetail{"invalid_request", err.Error()}, 0
	case errors.Is(err, ErrUnknownModel):
		return http.StatusNotFound, ErrorDetail{"unknown_model", err.Error()}, 0
	case errors.Is(err, context.DeadlineExceeded):
		return http.StatusGatewayTimeout, ErrorDetail{"timeout", "No upstream answered in time."}, 0
	}
	statuses := statusErrors(err)
	if len(statuses) == 0 {
		return http.StatusInternalServerError, ErrorDetail{"internal", "The gateway failed."}, 0
	}
	busy, wait := true, time.Duration(0)
	for _, each := range statuses {
		switch {
		case each.Status == http.StatusTooManyRequests:
			if each.RetryAfter > 0 && (wait == 0 || each.RetryAfter < wait) {
				wait = each.RetryAfter
			}
		case each.Status < 500:
			return http.StatusBadRequest, ErrorDetail{"invalid_request", "An upstream refused the request."}, 0
		default:
			busy = false
		}
	}
	if busy {
		return http.StatusTooManyRequests, ErrorDetail{"rate_limited", "Every upstream is busy. Try again later."}, wait
	}
	return http.StatusBadGateway, ErrorDetail{"upstream_error", "No upstream could answer."}, 0
}

// statusErrors gives every StatusError in err's tree, however each was wrapped or joined.
func statusErrors(err error) []*StatusError {
	switch err := err.(type) {
	case *StatusError:
		return []*StatusError{err}
	case interface{ Unwrap() error }:
		return statusErrors(err.Unwrap())
	case interface{ Unwrap() []error }:
		var found []*StatusError
		for _, each := range err.Unwrap() {
			found = append(found, statusErrors(each)...)
		}
		return found
	}
	return nil
}
