package checks

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"testing"
	"time"

	"example/gateway"
)

var caller = &http.Client{Timeout: 5 * time.Second}

// A slow handler reads the request, then writes its reply after its wait, or stops when the
// request's context is done. It closes done once it has returned.
type slow struct {
	wait time.Duration
	in   chan struct{}
	done chan struct{}
}

func newSlow(wait time.Duration) *slow {
	return &slow{wait: wait, in: make(chan struct{}), done: make(chan struct{})}
}

func (s *slow) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	defer close(s.done)
	io.Copy(io.Discard, r.Body)
	close(s.in)
	select {
	case <-time.After(s.wait):
		io.WriteString(w, "done")
	case <-r.Context().Done():
	}
}

// run starts Run with handler and a grace of grace, on a port of its own, and gives its address,
// a cancel that shuts it down, and the channel Run's error comes on.
func run(t *testing.T, handler http.Handler, grace time.Duration) (string, context.CancelFunc, chan error) {
	t.Helper()
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	stopped := make(chan error, 1)
	go func() {
		stopped <- gateway.Run(ctx, gateway.NewHTTPServer(handler), listener, grace)
	}()
	t.Cleanup(func() {
		cancel()
		listener.Close()
	})
	return listener.Addr().String(), cancel, stopped
}

type answer struct {
	text string
	err  error
}

// ask posts to address, and gives the reply's text or the error on the channel it returns.
func ask(address string) chan answer {
	answers := make(chan answer, 1)
	go func() {
		response, err := caller.Post("http://"+address+"/", "text/plain", nil)
		if err != nil {
			answers <- answer{err: err}
			return
		}
		defer response.Body.Close()
		text, err := io.ReadAll(response.Body)
		answers <- answer{text: string(text), err: err}
	}()
	return answers
}

func TestRunInUse(t *testing.T) {
	t.Run("tst_i72gxr Lets a request in flight finish", func(t *testing.T) {
		handler := newSlow(300 * time.Millisecond)
		address, cancel, _ := run(t, handler, 5*time.Second)
		answers := ask(address)
		<-handler.in
		cancel()
		if got := <-answers; got.err != nil || got.text != "done" {
			t.Errorf("got %q and the error %v for a request in flight at the shutdown, want its reply, done", got.text, got.err)
		}
	})
	t.Run("tst_3nxkxg Returns once the requests in flight are done", func(t *testing.T) {
		handler := newSlow(300 * time.Millisecond)
		address, cancel, stopped := run(t, handler, 5*time.Second)
		ask(address)
		<-handler.in
		cancel()
		select {
		case <-stopped:
		case <-time.After(3 * time.Second):
			t.Fatalf("Run hadn't returned 3 seconds after the shutdown")
		}
		select {
		case <-handler.done:
		default:
			t.Errorf("Run returned while a request was still in flight")
		}
	})
	t.Run("tst_ca82u6 Closes what's still open once the grace is up, with an error", func(t *testing.T) {
		handler := newSlow(time.Minute)
		address, cancel, stopped := run(t, handler, 200*time.Millisecond)
		answers := ask(address)
		<-handler.in
		cancel()
		select {
		case err := <-stopped:
			if !errors.Is(err, context.DeadlineExceeded) {
				t.Errorf("got the error %v once the grace was up, want one that is DeadlineExceeded", err)
			}
		case <-time.After(3 * time.Second):
			t.Fatalf("Run hadn't returned 3 seconds after the shutdown, with a grace of 200ms")
		}
		select {
		case got := <-answers:
			if got.err == nil {
				t.Errorf("got the reply %q, want the connection closed", got.text)
			}
		case <-time.After(2 * time.Second):
			t.Errorf("the request was still open 2 seconds after Run returned")
		}
	})
	t.Run("tst_kdjyi4 Gives the error when it can't serve", func(t *testing.T) {
		listener, err := net.Listen("tcp", "127.0.0.1:0")
		if err != nil {
			t.Fatal(err)
		}
		listener.Close()
		stopped := make(chan error, 1)
		go func() {
			stopped <- gateway.Run(context.Background(), gateway.NewHTTPServer(http.NotFoundHandler()), listener, time.Second)
		}()
		select {
		case err := <-stopped:
			if err == nil || errors.Is(err, http.ErrServerClosed) {
				t.Errorf("got the error %v on a closed listener, want the one Serve gave", err)
			}
		case <-time.After(2 * time.Second):
			t.Errorf("Run was still waiting 2 seconds after it couldn't serve on a closed listener")
		}
	})
}
