package gateway

import "context"

// A Bucket lets requests through at a steady rate, with bursts: it holds up to burst tokens,
// gains rate tokens a second, and each request takes one. It starts full.
type Bucket struct {
}

// NewBucket gives a full bucket that gains rate tokens a second and holds up to burst.
func NewBucket(rate float64, burst int) *Bucket {
	return &Bucket{}
}

// Allow takes a token if there is one, and reports whether it did.
func (b *Bucket) Allow() bool {
	return true
}

// Wait takes a token, waiting for one if it must. It gives ctx's error, and takes no token, if
// ctx is done first.
func (b *Bucket) Wait(ctx context.Context) error {
	return nil
}

// A Limiter gives each key a bucket of its own, all with the same rate and burst.
type Limiter struct {
}

// NewLimiter gives a limiter whose buckets gain rate tokens a second and hold up to burst.
func NewLimiter(rate float64, burst int) *Limiter {
	return &Limiter{}
}

// For gives key's bucket, the same one each time, made full the first time key asks.
func (l *Limiter) For(key string) *Bucket {
	return &Bucket{}
}
