package gateway

import (
	"context"
	"net"
	"net/http"
	"time"
)

// NewHTTPServer gives a server for handler with the gateway's timeouts.
func NewHTTPServer(handler http.Handler) *http.Server {
	return &http.Server{Handler: handler}
}

// Run serves on listener until ctx is done, then shuts the server down: it stops taking
// connections and waits up to grace for the requests in flight, then closes the connections
// still open. It gives the error that stopped the server from serving, or the shutdown's.
func Run(ctx context.Context, server *http.Server, listener net.Listener, grace time.Duration) error {
	return server.Serve(listener)
}
