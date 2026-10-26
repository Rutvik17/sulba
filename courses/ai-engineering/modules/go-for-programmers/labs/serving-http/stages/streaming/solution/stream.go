package gateway

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// A Chunk is one event of a streamed reply, in the shape of OpenAI's.
type Chunk struct {
	Object  string        `json:"object"`
	Model   string        `json:"model"`
	Choices []ChunkChoice `json:"choices"`
}

// A ChunkChoice is a chunk's piece of a reply.
type ChunkChoice struct {
	Index int   `json:"index"`
	Delta Delta `json:"delta"`
}

// A Delta is the text a chunk adds.
type Delta struct {
	Content string `json:"content"`
}

// Stream asks the upstream for its reply as server-sent events, and calls each with each piece of
// the reply's text as it arrives. It stops at the first error each gives, and gives that. Once
// the stream ends, it gives the reply, with the whole text.
func (u *HTTPUpstream) Stream(ctx context.Context, request ChatRequest, each func(piece string) error) (Reply, error) {
	request.Stream = true
	body, err := json.Marshal(request)
	if err != nil {
		return Reply{}, err
	}
	post, err := http.NewRequestWithContext(ctx, http.MethodPost, u.baseURL+"/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return Reply{}, err
	}
	post.Header.Set("Content-Type", "application/json")
	post.Header.Set("Accept", "text/event-stream")
	response, err := u.client.Do(post)
	if err != nil {
		return Reply{}, err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return Reply{}, statusError(response)
	}
	var text strings.Builder
	lines := bufio.NewScanner(response.Body)
	lines.Buffer(make([]byte, 64<<10), maxReply)
	for lines.Scan() {
		data, found := strings.CutPrefix(lines.Text(), "data:")
		if !found {
			continue
		}
		data = strings.TrimPrefix(data, " ")
		if data == "[DONE]" {
			return Reply{Upstream: u.name, Content: text.String()}, nil
		}
		var chunk Chunk
		if err := json.Unmarshal([]byte(data), &chunk); err != nil {
			return Reply{}, fmt.Errorf("reading %s's stream: %w", u.name, err)
		}
		for _, choice := range chunk.Choices {
			if choice.Delta.Content == "" {
				continue
			}
			text.WriteString(choice.Delta.Content)
			if err := each(choice.Delta.Content); err != nil {
				return Reply{}, err
			}
		}
	}
	if err := lines.Err(); err != nil {
		return Reply{}, fmt.Errorf("reading %s's stream: %w", u.name, err)
	}
	return Reply{}, fmt.Errorf("%s's stream ended before [DONE]", u.name)
}

// Relay answers a request that asked to stream with the upstream's reply as server-sent events,
// as OpenAI's API sends them: a chunk for each piece, flushed as it's written, then
// data: [DONE]. A failure before the first piece is answered as an error. A failure after it
// ends the stream without [DONE].
func Relay(w http.ResponseWriter, r *http.Request, upstream *HTTPUpstream, request ChatRequest) error {
	flusher := http.NewResponseController(w)
	started := false
	send := func(data string) error {
		if !started {
			w.Header().Set("Content-Type", "text/event-stream")
			w.Header().Set("Cache-Control", "no-cache")
			started = true
		}
		if _, err := fmt.Fprintf(w, "data: %s\n\n", data); err != nil {
			return err
		}
		return flusher.Flush()
	}
	_, err := upstream.Stream(r.Context(), request, func(piece string) error {
		chunk, err := json.Marshal(Chunk{
			Object:  "chat.completion.chunk",
			Model:   request.Model,
			Choices: []ChunkChoice{{Delta: Delta{Content: piece}}},
		})
		if err != nil {
			return err
		}
		return send(string(chunk))
	})
	if err != nil {
		if !started {
			WriteError(w, err)
		}
		return err
	}
	return send("[DONE]")
}
