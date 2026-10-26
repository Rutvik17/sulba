Retries help when one call in a hundred fails. In an outage, when every call fails, they multiply the load on upstreams that are already down. The gateway gives each client a retry budget, which allows retries only while they're a small share of its requests.

In `budget.go`, write:

- `NewBudget(ratio, floor, window)`, and `budget.Request()`, which counts a request's first call.
- `budget.Retry()`, which counts a retry and gives `true` when, with it, the retries in the last `window` are no more than `floor` plus `ratio` of the requests in it. Otherwise it counts nothing and gives `false`. A request or retry exactly `window` old is out of the window.
- `RetryWithin(ctx, budget, backoff, call)`, which is your `Retry` with a budget. It counts the request, and before each wait, once it knows the wait fits before `ctx`'s deadline, it asks the budget for the retry. When the budget refuses, it gives the last error at once, wrapped with a message that says the retry budget is spent.

Every request of a client shares its budget, at once, so a budget is safe for many goroutines to use.

```go
func NewBudget(ratio float64, floor int, window time.Duration) *Budget
func (b *Budget) Request()
func (b *Budget) Retry() bool
func RetryWithin(ctx context.Context, budget *Budget, backoff Backoff, call func(context.Context) error) error
```

The tests show you which of their cases pass, but not what they gave or expected. Checks then send a stream of requests through a budget as the gateway will set it, a ratio of 0.1 with a floor of 10 a minute, before it ships.
