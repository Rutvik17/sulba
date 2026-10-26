package gateway

import (
	"context"
	"math"
	"sync"
	"time"
)

// A Bucket lets requests through at a steady rate, with bursts: it holds up to burst tokens,
// gains rate tokens a second, and each request takes one. It starts full.
type Bucket struct {
	mu     sync.Mutex
	rate   float64
	burst  float64
	tokens float64
	last   time.Time
}

// NewBucket gives a full bucket that gains rate tokens a second and holds up to burst.
func NewBucket(rate float64, burst int) *Bucket {
	return &Bucket{rate: rate, burst: float64(burst), tokens: float64(burst), last: time.Now()}
}

// refill adds the tokens gained since the last refill. The caller holds b.mu.
func (b *Bucket) refill() {
	now := time.Now()
	b.tokens = min(b.burst, b.tokens+now.Sub(b.last).Seconds()*b.rate)
	b.last = now
}

// Allow takes a token if there is one, and reports whether it did.
func (b *Bucket) Allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.refill()
	if b.tokens < 1 {
		return false
	}
	b.tokens--
	return true
}

// Wait takes a token, waiting for one if it must. It gives ctx's error, and takes no token, if
// ctx is done first.
func (b *Bucket) Wait(ctx context.Context) error {
	for {
		b.mu.Lock()
		b.refill()
		if b.tokens >= 1 {
			b.tokens--
			b.mu.Unlock()
			return nil
		}
		// Rounded up, so the wait ends with a whole token.
		wait := time.Duration(math.Ceil((1 - b.tokens) / b.rate * float64(time.Second)))
		b.mu.Unlock()
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
			return ctx.Err()
		case <-timer.C:
		}
	}
}

// A Limiter gives each key a bucket of its own, all with the same rate and burst.
type Limiter struct {
	mu      sync.Mutex
	rate    float64
	burst   int
	buckets map[string]*Bucket
}

// NewLimiter gives a limiter whose buckets gain rate tokens a second and hold up to burst.
func NewLimiter(rate float64, burst int) *Limiter {
	return &Limiter{rate: rate, burst: burst, buckets: map[string]*Bucket{}}
}

// For gives key's bucket, the same one each time, made full the first time key asks.
func (l *Limiter) For(key string) *Bucket {
	l.mu.Lock()
	defer l.mu.Unlock()
	bucket, found := l.buckets[key]
	if !found {
		bucket = NewBucket(l.rate, l.burst)
		l.buckets[key] = bucket
	}
	return bucket
}
