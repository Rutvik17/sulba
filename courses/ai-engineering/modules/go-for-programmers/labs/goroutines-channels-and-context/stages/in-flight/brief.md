A model server runs a few requests at once, and more only queue up inside it, where the gateway can't see them or call them off. So the gateway keeps its own limit on what's in flight to each upstream.

In `flight.go`, write:

- `NewGate(n)` and `gate.Do(ctx, call)`, which runs `call` once fewer than `n` calls are running through the gate, and gives its error. A call that fails or panics frees its place. If `ctx` is done before there's room, `Do` gives `ctx`'s error without running `call`.
- `gate.InFlight()`, which gives how many calls are running through the gate.
- `ChatAll(ctx, gate, upstream, requests)`, which sends every request to `upstream` at once, each from a goroutine of its own and through `gate`, and gives the replies in the requests' order. The first error cancels the requests still running, and `ChatAll` gives that error once they have all stopped.

```go
func NewGate(n int) *Gate
func (g *Gate) Do(ctx context.Context, call func(context.Context) error) error
func (g *Gate) InFlight() int
func ChatAll(ctx context.Context, gate *Gate, upstream Upstream, requests []ChatRequest) ([]Reply, error)
```
