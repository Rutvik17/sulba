package gateway

import (
	"errors"
	"fmt"
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
	return Routes{}, nil
}

// For gives the upstreams for model, in order, in a slice of the caller's own.
func (r Routes) For(model string) ([]string, error) {
	return nil, nil
}

// Models gives the models the routes name, sorted.
func (r Routes) Models() []string {
	return nil
}
