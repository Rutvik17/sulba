package tests

import (
	"errors"
	"slices"
	"strings"
	"testing"

	"example/gateway"
)

const table = `# Each model, and the upstreams that serve it.
qwen: local, backup

  gemma :spare
llama: local,backup , spare
`

func parse(t *testing.T, text string) gateway.Routes {
	t.Helper()
	routes, err := gateway.ParseRoutes(text)
	if err != nil {
		t.Fatalf("got the error %v, want none", err)
	}
	return routes
}

// lineError gives the LineError of parsing text, or fails the test.
func lineError(t *testing.T, text string, line int) *gateway.LineError {
	t.Helper()
	_, err := gateway.ParseRoutes(text)
	wrong, ok := errors.AsType[*gateway.LineError](err)
	if !ok {
		t.Fatalf("got the error %v, want a *LineError for line %d", err, line)
	}
	if wrong.Line != line {
		t.Fatalf("got a LineError for line %d, want one for line %d", wrong.Line, line)
	}
	return wrong
}

func TestRoutes(t *testing.T) {
	t.Run("tst_5aakhf Reads each model's upstreams in order", func(t *testing.T) {
		routes := parse(t, table)
		for model, want := range map[string][]string{
			"qwen":  {"local", "backup"},
			"gemma": {"spare"},
			"llama": {"local", "backup", "spare"},
		} {
			got, err := routes.For(model)
			if err != nil || !slices.Equal(got, want) {
				t.Errorf("for %s, got %q and the error %v, want %q", model, got, err, want)
			}
		}
	})
	t.Run("tst_dfg6is Gives an unknown model ErrUnknownModel, naming it", func(t *testing.T) {
		_, err := parse(t, table).For("gpt-9")
		if !errors.Is(err, gateway.ErrUnknownModel) {
			t.Fatalf("got the error %v, want one that wraps ErrUnknownModel", err)
		}
		if !strings.Contains(err.Error(), "gpt-9") {
			t.Errorf("got the message %q, want it to name the model, gpt-9", err.Error())
		}
		var none gateway.Routes
		if _, err := none.For("qwen"); !errors.Is(err, gateway.ErrUnknownModel) {
			t.Errorf("with no routes at all, got the error %v, want one that wraps ErrUnknownModel", err)
		}
	})
	t.Run("tst_ots47p Gives each caller a slice of its own", func(t *testing.T) {
		routes := parse(t, table)
		got, _ := routes.For("llama")
		if len(got) != 3 {
			t.Fatalf("got %q, want llama's three upstreams", got)
		}
		got[0] = "changed"
		got = append(got[:1], "added")
		_ = got
		again, _ := routes.For("llama")
		if want := []string{"local", "backup", "spare"}; !slices.Equal(again, want) {
			t.Errorf("after a caller changed its slice, got %q, want %q", again, want)
		}
	})
	t.Run("tst_ecbj3e Lists the models in order", func(t *testing.T) {
		got := parse(t, table).Models()
		if want := []string{"gemma", "llama", "qwen"}; !slices.Equal(got, want) {
			t.Errorf("got %q, want %q", got, want)
		}
	})
	t.Run("tst_s4ab7w Names the line with no colon, or no model", func(t *testing.T) {
		lineError(t, "qwen: local\n\n# a comment\ngemma spare\n", 4)
		lineError(t, "qwen: local\n: spare\n", 2)
	})
	t.Run("tst_gnrkwl Refuses a model with no upstreams, or routed twice", func(t *testing.T) {
		wrong := lineError(t, "qwen: local\ngemma:  \n", 2)
		if !strings.Contains(wrong.Error(), "gemma") {
			t.Errorf("got the message %q, want it to name the model, gemma", wrong.Error())
		}
		lineError(t, "qwen: local\ngemma: spare\nqwen: backup\n", 3)
	})
	t.Run("tst_55yba7 Refuses an upstream listed twice for a model", func(t *testing.T) {
		wrong := lineError(t, "qwen: local, backup, local\n", 1)
		if !strings.Contains(wrong.Error(), "local") {
			t.Errorf("got the message %q, want it to name the upstream, local", wrong.Error())
		}
	})
}
