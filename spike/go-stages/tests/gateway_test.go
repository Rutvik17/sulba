package tests

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"testing/synctest"
	"time"

	"example/gateway"
)

func TestLimiter(t *testing.T) {
	t.Run("tst_aaaaaa waits a tenth of a second for its second token", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			l := gateway.NewLimiter(10, 1)
			start := time.Now()
			for range 2 {
				if err := l.Wait(context.Background()); err != nil {
					t.Fatal(err)
				}
			}
			if got := time.Since(start); got != 100*time.Millisecond {
				t.Errorf("waited %v, want 100ms", got)
			}
		})
	})
	t.Run("tst_bbbbbb a failing one", func(t *testing.T) {
		if got, want := 1, 2; got != want {
			t.Errorf("got %d, want %d", got, want)
		}
	})
	t.Run("tst_dddddd gives up when its context ends", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			l := gateway.NewLimiter(1, 1)
			ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
			defer cancel()
			start := time.Now()
			_ = l.Wait(ctx)
			err := l.Wait(ctx)
			if !errors.Is(err, context.DeadlineExceeded) || time.Since(start) != 50*time.Millisecond {
				t.Errorf("got %v after %v, want the deadline after 50ms", err, time.Since(start))
			}
		})
	})
}

func TestProxy(t *testing.T) {
	t.Run("tst_cccccc passes the request on", func(t *testing.T) {
		upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			_, _ = io.WriteString(w, "from "+r.URL.Path)
		}))
		defer upstream.Close()
		front := httptest.NewServer(gateway.Proxy(upstream.URL, upstream.Client()))
		defer front.Close()
		resp, err := front.Client().Get(front.URL + "/v1/models")
		if err != nil {
			t.Fatal(err)
		}
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		if string(body) != "from /v1/models" {
			t.Errorf("got %q", body)
		}
	})
}

func BenchmarkLimiter(b *testing.B) {
	l := gateway.NewLimiter(1e12, 1e12)
	for b.Loop() {
		_ = l.Wait(context.Background())
	}
}
