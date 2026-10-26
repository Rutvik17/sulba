package gateway

import (
	"errors"
	"fmt"
	"maps"
	"slices"
	"strings"
)

// Routes gives each model a caller can ask for the upstreams that serve it, in the order to try
// them.
type Routes map[string][]string

var ErrUnknownModel = errors.New("no route for the model")

// A LineError says which line of the routes is wrong, and how.
type LineError struct {
	Line    int
	Problem string
}

func (e *LineError) Error() string {
	return fmt.Sprintf("line %d %s", e.Line, e.Problem)
}

// ParseRoutes reads routes, a model a line, with its upstreams after a colon, separated by
// commas, as in "qwen: local, backup". It skips blank lines and lines that start with #.
func ParseRoutes(text string) (Routes, error) {
	routes := Routes{}
	for i, line := range strings.Split(text, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		model, list, found := strings.Cut(line, ":")
		model = strings.TrimSpace(model)
		switch {
		case !found:
			return nil, &LineError{Line: i + 1, Problem: "has no colon"}
		case model == "":
			return nil, &LineError{Line: i + 1, Problem: "names no model"}
		}
		if _, routed := routes[model]; routed {
			return nil, &LineError{Line: i + 1, Problem: "routes " + model + " a second time"}
		}
		var upstreams []string
		for _, name := range strings.Split(list, ",") {
			name = strings.TrimSpace(name)
			if name == "" {
				continue
			}
			if slices.Contains(upstreams, name) {
				return nil, &LineError{Line: i + 1, Problem: "lists " + name + " twice"}
			}
			upstreams = append(upstreams, name)
		}
		if len(upstreams) == 0 {
			return nil, &LineError{Line: i + 1, Problem: "gives " + model + " no upstreams"}
		}
		routes[model] = upstreams
	}
	return routes, nil
}

// For gives the upstreams for model, in order, in a slice of the caller's own.
func (r Routes) For(model string) ([]string, error) {
	upstreams, found := r[model]
	if !found {
		return nil, fmt.Errorf("%w %q", ErrUnknownModel, model)
	}
	return slices.Clone(upstreams), nil
}

// Models gives the models the routes name, sorted.
func (r Routes) Models() []string {
	return slices.Sorted(maps.Keys(r))
}
