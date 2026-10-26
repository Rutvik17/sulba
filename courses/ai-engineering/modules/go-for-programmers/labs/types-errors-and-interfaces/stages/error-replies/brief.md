When a request fails, the gateway answers with a status and a JSON body that says what went wrong:

```json
{"error": {"type": "invalid_request", "message": "the request names no model"}}
```

In `failures.go`, `WriteError(w, err)` answers a request that failed with `err`, with `Content-Type: application/json`. The first row that fits `err` gives the answer:

| When `err` holds | Status | `type` | `message` |
| --- | --- | --- | --- |
| `ErrNotJSON`, `ErrNoModel`, `ErrNoMessages` or a `*FieldError` | 400 | `invalid_request` | `err`'s own |
| `ErrUnknownModel` | 404 | `unknown_model` | `err`'s own |
| `context.DeadlineExceeded` | 504 | `timeout` | `No upstream answered in time.` |
| a `*StatusError` from 400 to 499, other than 429 | 400 | `invalid_request` | `An upstream refused the request.` |
| `*StatusError`s that are all 429 | 429 | `rate_limited` | `Every upstream is busy. Try again later.` |
| any other `*StatusError` | 502 | `upstream_error` | `No upstream could answer.` |
| anything else | 500 | `internal` | `The gateway failed.` |

`err` can hold its errors wrapped and joined in any way `Fallback` and the code around it might. A 429 also tells the caller how long to wait, with `Retry-After`: the soonest wait any of the upstreams gave, in whole seconds, rounded up. When none of them gave one, there's no `Retry-After`.

```go
func WriteError(w http.ResponseWriter, err error)
```

The tests show you which of their cases pass, but not what they gave or expected. Checks then test what the answers need before the gateway ships.
