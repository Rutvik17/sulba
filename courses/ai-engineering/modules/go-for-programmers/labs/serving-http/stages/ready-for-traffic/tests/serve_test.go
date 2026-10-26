package tests

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"testing"
	"time"

	"example/gateway"
)

var caller = &http.Client{Timeout: 3 * time.Second}

func ok(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "ok")
}

// start runs a server for handler on a port of its own, and gives its listener, a cancel that
// shuts it down, and the channel Run's error comes on.
func start(t *testing.T, handler http.HandlerFunc) (*net.TCPListener, context.CancelFunc, chan error) {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	stopped := make(chan error, 1)
	go func() {
		stopped <- gateway.Run(ctx, gateway.NewHTTPServer(handler), listener, time.Second)
	}()
	t.Cleanup(func() {
		cancel()
		listener.Close()
	})
	return listener.(*net.TCPListener), cancel, stopped
}

// within gives Run's error, or fails the test if Run hasn't returned within wait.
func within(t *testing.T, stopped chan error, wait time.Duration) error {
	t.Helper()
	select {
	case err := <-stopped:
		return err
	case <-time.After(wait):
		t.Fatalf("Run hadn't returned %v after the context was done", wait)
		return nil
	}
}

func TestHTTPServer(t *testing.T) {
	server := gateway.NewHTTPServer(http.HandlerFunc(ok))
	t.Run("tst_e241yj Reads a request's headers within 5 seconds", func(t *testing.T) {
		if server.ReadHeaderTimeout != 5*time.Second {
			t.Errorf("got a ReadHeaderTimeout of %v, want 5s", server.ReadHeaderTimeout)
		}
	})
	t.Run("tst_0q80p0 Reads the whole request within 30 seconds", func(t *testing.T) {
		if server.ReadTimeout != 30*time.Second {
			t.Errorf("got a ReadTimeout of %v, want 30s", server.ReadTimeout)
		}
	})
	t.Run("tst_xrr88x Gives a reply 5 minutes to write", func(t *testing.T) {
		if server.WriteTimeout != 5*time.Minute {
			t.Errorf("got a WriteTimeout of %v, want 5m0s", server.WriteTimeout)
		}
	})
	t.Run("tst_1bi07f Closes a connection left idle for 2 minutes", func(t *testing.T) {
		if server.IdleTimeout != 2*time.Minute {
			t.Errorf("got an IdleTimeout of %v, want 2m0s", server.IdleTimeout)
		}
	})
	t.Run("tst_3n6w31 Serves with the handler it's given", func(t *testing.T) {
		if server.Handler == nil {
			t.Errorf("got a server with no handler")
		}
	})
}

func TestRun(t *testing.T) {
	t.Run("tst_y94xyc Serves requests on the listener", func(t *testing.T) {
		listener, _, _ := start(t, ok)
		response, err := caller.Get("http://" + listener.Addr().String() + "/")
		if err != nil {
			t.Fatal(err)
		}
		defer response.Body.Close()
		if text, _ := io.ReadAll(response.Body); string(text) != "ok\n" {
			t.Errorf("got %q, want the handler's ok", text)
		}
	})
	t.Run("tst_cofyih Gives nil once it has shut down", func(t *testing.T) {
		_, cancel, stopped := start(t, ok)
		cancel()
		if err := within(t, stopped, 2*time.Second); err != nil {
			t.Errorf("got the error %v, want nil", err)
		}
	})
	t.Run("tst_4dkmqz Closes the listener once it has shut down", func(t *testing.T) {
		listener, cancel, stopped := start(t, ok)
		cancel()
		within(t, stopped, 2*time.Second)
		listener.SetDeadline(time.Now().Add(time.Second))
		if connection, err := listener.Accept(); !errors.Is(err, net.ErrClosed) {
			if err == nil {
				connection.Close()
			}
			t.Errorf("the listener was still open after Run returned")
		}
	})
}
