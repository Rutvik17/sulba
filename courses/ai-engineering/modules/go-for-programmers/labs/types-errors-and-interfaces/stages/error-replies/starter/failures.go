package gateway

import "net/http"

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
	w.WriteHeader(http.StatusInternalServerError)
}
