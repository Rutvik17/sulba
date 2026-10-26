package gateway

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"
)

// NewHTTPServer gives a server for handler with the gateway's timeouts: 5 seconds to read a
// request's headers and 30 to read all of it, 5 minutes to write a reply, which leaves time to
// stream a long one, and 2 minutes before it closes an idle connection.
func NewHTTPServer(handler http.Handler) *http.Server {
	return &http.Server{
		Handler:           handler,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      5 * time.Minute,
		IdleTimeout:       2 * time.Minute,
	}
}

// Run serves on listener until ctx is done, then shuts the server down: it stops taking
// connections and waits up to grace for the requests in flight, then closes the connections
// still open. It gives the error that stopped the server from serving, or the shutdown's.
func Run(ctx context.Context, server *http.Server, listener net.Listener, grace time.Duration) error {
	served := make(chan error, 1)
	go func() {
		served <- server.Serve(listener)
	}()
	select {
	case err := <-served:
		return err
	case <-ctx.Done():
	}
	stopping, cancel := context.WithTimeout(context.WithoutCancel(ctx), grace)
	defer cancel()
	if err := server.Shutdown(stopping); err != nil {
		server.Close()
		return fmt.Errorf("shutting down: %w", err)
	}
	return nil
}
