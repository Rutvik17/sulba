The gateway sends each model's requests to the upstreams that serve it, the model servers it can ask, in the order to try them. Its routes come from a file, with a model a line:

```text
# Each model, and the upstreams that serve it.
qwen: local, backup
gemma: spare
```

In `routes.go`, write:

- `ParseRoutes(text)`, which reads the routes. It skips blank lines and lines that start with `#`, and trims the spaces around each name. A line with no colon, or no model before its colon, gives a `*LineError` for the line, counting from 1. So does a model routed a second time, a model with no upstreams, whose message names the model, and an upstream listed twice on a line, whose message names the upstream.
- `routes.For(model)`, which gives the model's upstreams in order, in a slice of the caller's own: a caller that changes it changes nothing in the routes. A model with no route gives an error that wraps `ErrUnknownModel` and names the model, and so does any model when the routes are nil.
- `routes.Models()`, which gives the models, sorted.

```go
func ParseRoutes(text string) (Routes, error)
func (r Routes) For(model string) ([]string, error)
func (r Routes) Models() []string
```
