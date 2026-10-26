package tests

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"slices"
	"strings"
	"testing"
	"time"

	"example/gateway"
)

// A caller that gives up on an answer after 3 seconds, so a stream that never comes fails a test
// rather than holding it.
var caller = &http.Client{Timeout: 3 * time.Second}

var asked = gateway.ChatRequest{Model: "qwen", Messages: []gateway.Message{{Role: "user", Content: "When do you open?"}}}

// A model server that streams its pieces as chunks, flushing each, then data: [DONE]. Before each
// piece after the first, it waits for next, when next isn't nil. It closes gone, when gone isn't
// nil, once its caller has hung up.
type streamer struct {
	pieces []string
	extra  string
	next   chan struct{}
	gone   chan struct{}
	asked  gateway.ChatRequest
}

func (s *streamer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	json.NewDecoder(r.Body).Decode(&s.asked)
	w.Header().Set("Content-Type", "text/event-stream")
	flusher := http.NewResponseController(w)
	io.WriteString(w, s.extra)
	for i, piece := range s.pieces {
		if i > 0 && s.next != nil {
			select {
			case <-s.next:
			case <-r.Context().Done():
				if s.gone != nil {
					close(s.gone)
				}
				return
			}
		}
		fmt.Fprintf(w, "data: {\"choices\": [{\"index\": 0, \"delta\": {\"content\": %q}}]}\n\n", piece)
		flusher.Flush()
	}
	io.WriteString(w, "data: [DONE]\n\n")
}

func upstreamFor(t *testing.T, handler http.Handler) *gateway.HTTPUpstream {
	t.Helper()
	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)
	return gateway.NewHTTPUpstream("local", server.URL, server.Client())
}

// relaying starts the gateway's side: a server that relays every request to upstream.
func relaying(t *testing.T, upstream *gateway.HTTPUpstream) *httptest.Server {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gateway.Relay(w, r, upstream, asked)
	}))
	t.Cleanup(server.Close)
	return server
}

// event reads the next event's data from a stream, or fails the test after a second.
func event(t *testing.T, stream *bufio.Reader) string {
	t.Helper()
	read := make(chan string, 1)
	go func() {
		for {
			line, err := stream.ReadString('\n')
			if data, found := strings.CutPrefix(strings.TrimRight(line, "\n"), "data: "); found {
				read <- data
				return
			}
			if err != nil {
				read <- "(the stream ended)"
				return
			}
		}
	}()
	select {
	case data := <-read:
		return data
	case <-time.After(time.Second):
		t.Fatalf("no event came within a second")
		return ""
	}
}

func TestStream(t *testing.T) {
	t.Run("tst_brdtg6 Asks the upstream to stream, and gives each piece as it arrives", func(t *testing.T) {
		model := &streamer{pieces: []string{"At", " 9", "."}}
		var pieces []string
		reply, err := upstreamFor(t, model).Stream(context.Background(), asked, func(piece string) error {
			pieces = append(pieces, piece)
			return nil
		})
		if err != nil || reply.Content != "At 9." || !slices.Equal(pieces, []string{"At", " 9", "."}) {
			t.Fatalf("got %+v, the pieces %q and the error %v, want At, 9 and . and the reply At 9.", reply, pieces, err)
		}
		if !model.asked.Stream {
			t.Errorf("the upstream was asked %+v, want stream set", model.asked)
		}
	})
	t.Run("tst_iiz4mt Reads data with or without a space, and skips comments and other fields", func(t *testing.T) {
		model := &streamer{pieces: []string{"hi"}, extra: ": ping\n\nevent: message\nid: 1\n\ndata:{\"choices\": [{\"index\": 0, \"delta\": {\"content\": \"Oh, \"}}]}\n\n"}
		reply, err := upstreamFor(t, model).Stream(context.Background(), asked, func(string) error { return nil })
		if err != nil || reply.Content != "Oh, hi" {
			t.Errorf("got %+v and the error %v, want Oh, hi", reply, err)
		}
	})
	t.Run("tst_mckely Gives a StatusError when the upstream refuses", func(t *testing.T) {
		upstream := upstreamFor(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.Error(w, "down", 503)
		}))
		_, err := upstream.Stream(context.Background(), asked, func(string) error { return nil })
		if status, ok := errors.AsType[*gateway.StatusError](err); !ok || status.Status != 503 {
			t.Errorf("got the error %v, want a StatusError of 503", err)
		}
	})
	t.Run("tst_ix21gu Stops at the first error from each, and gives it", func(t *testing.T) {
		stop := errors.New("the caller went away")
		calls := 0
		_, err := upstreamFor(t, &streamer{pieces: []string{"a", "b", "c"}}).Stream(context.Background(), asked, func(string) error {
			calls++
			return stop
		})
		if err != stop || calls != 1 {
			t.Errorf("got the error %v after %d pieces, want each's error after 1", err, calls)
		}
	})
}

func TestRelay(t *testing.T) {
	t.Run("tst_0fbabl Sends each piece as soon as it arrives", func(t *testing.T) {
		model := &streamer{pieces: []string{"At", " 9."}, next: make(chan struct{})}
		response, err := caller.Get(relaying(t, upstreamFor(t, model)).URL)
		if err != nil {
			t.Fatalf("got the error %v", err)
		}
		defer response.Body.Close()
		stream := bufio.NewReader(response.Body)
		first := event(t, stream)
		close(model.next)
		var chunk gateway.Chunk
		if json.Unmarshal([]byte(first), &chunk) != nil || len(chunk.Choices) != 1 || chunk.Choices[0].Delta.Content != "At" {
			t.Errorf("got the first event %q, want a chunk of At", first)
		}
	})
	t.Run("tst_h94gev Streams OpenAI's chunks, then data: [DONE]", func(t *testing.T) {
		response, err := caller.Get(relaying(t, upstreamFor(t, &streamer{pieces: []string{"At", " 9."}})).URL)
		if err != nil {
			t.Fatalf("got the error %v", err)
		}
		defer response.Body.Close()
		if got := response.Header.Get("Content-Type"); got != "text/event-stream" {
			t.Errorf("got the Content-Type %q, want text/event-stream", got)
		}
		stream := bufio.NewReader(response.Body)
		var text string
		for range 2 {
			var chunk gateway.Chunk
			json.Unmarshal([]byte(event(t, stream)), &chunk)
			if chunk.Object != "chat.completion.chunk" || chunk.Model != "qwen" || len(chunk.Choices) != 1 {
				t.Fatalf("got the chunk %+v, want a chat.completion.chunk of qwen's reply", chunk)
			}
			text += chunk.Choices[0].Delta.Content
		}
		if last := event(t, stream); text != "At 9." || last != "[DONE]" {
			t.Errorf("got %q, then %q, want At 9. then [DONE]", text, last)
		}
	})
	t.Run("tst_f5i2n5 Answers a refusal before the stream as an error", func(t *testing.T) {
		upstream := upstreamFor(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.Error(w, "down", 503)
		}))
		response, err := caller.Get(relaying(t, upstream).URL)
		if err != nil {
			t.Fatalf("got the error %v", err)
		}
		defer response.Body.Close()
		var body gateway.ErrorBody
		json.NewDecoder(response.Body).Decode(&body)
		if response.StatusCode != 502 || body.Error.Type != "upstream_error" {
			t.Errorf("got %d %+v, want 502 upstream_error", response.StatusCode, body)
		}
	})
	t.Run("tst_olnwln Stops the upstream's stream when the caller goes", func(t *testing.T) {
		model := &streamer{pieces: []string{"At", " 9."}, next: make(chan struct{}), gone: make(chan struct{})}
		ctx, cancel := context.WithCancel(context.Background())
		request, _ := http.NewRequestWithContext(ctx, "GET", relaying(t, upstreamFor(t, model)).URL, nil)
		response, err := caller.Do(request)
		if err != nil {
			t.Fatalf("got the error %v", err)
		}
		event(t, bufio.NewReader(response.Body))
		cancel()
		response.Body.Close()
		select {
		case <-model.gone:
		case <-time.After(2 * time.Second):
			t.Errorf("2 seconds after the caller went, the upstream was still being asked")
			close(model.next)
		}
	})
}
