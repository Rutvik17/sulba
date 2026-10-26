The gateway shares its upstreams among many keys, and one key's program stuck in a loop could take them all. A rate limit gives each key a fair share: a token bucket, which holds up to `burst` tokens, gains `rate` tokens a second, and lets a request through for each token it takes.

In `bucket.go`, write:

- `NewBucket(rate, burst)`, which gives a bucket that starts full.
- `bucket.Allow()`, which takes a token if there is one, and reports whether it did. However long a bucket waits, it never holds more than its burst.
- `bucket.Wait(ctx)`, which takes a token, waiting for one if there's none yet. If `ctx` is done first, it gives `ctx.Err()` and takes no token.
- `NewLimiter(rate, burst)` and `limiter.For(key)`, which gives each key a bucket of its own, the same one each time it asks.

Many requests ask a bucket at once, each in a goroutine of its own, so a bucket and a limiter guard what they keep with a `sync.Mutex`.

```go
func NewBucket(rate float64, burst int) *Bucket
func (b *Bucket) Allow() bool
func (b *Bucket) Wait(ctx context.Context) error
func NewLimiter(rate float64, burst int) *Limiter
func (l *Limiter) For(key string) *Bucket
```

The tests run inside `synctest.Test`, where `time.Now` and `time.Sleep` keep a fake clock, so an hour's wait takes no time.
