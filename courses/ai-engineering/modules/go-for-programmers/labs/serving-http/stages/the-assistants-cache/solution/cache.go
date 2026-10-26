package gateway

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"sync"
	"time"
)

// A Cache is an upstream that answers a request it has seen within its time to live with the
// reply it gave then, and asks its own upstream otherwise.
type Cache struct {
	upstream Upstream
	ttl      time.Duration
	mu       sync.Mutex
	entries  map[[32]byte]entry
}

type entry struct {
	reply   Reply
	expires time.Time
}

// NewCache gives a cache in front of upstream, whose replies live for ttl.
func NewCache(upstream Upstream, ttl time.Duration) *Cache {
	return &Cache{upstream: upstream, ttl: ttl, entries: map[[32]byte]entry{}}
}

// Name gives the name of the cache's upstream.
func (c *Cache) Name() string {
	return c.upstream.Name()
}

// Chat gives the reply the cache has for request, or asks its upstream for one and keeps it.
func (c *Cache) Chat(ctx context.Context, request ChatRequest) (Reply, error) {
	key := keyOf(request)
	c.mu.Lock()
	cached, found := c.entries[key]
	if found && time.Now().Before(cached.expires) {
		c.mu.Unlock()
		return cached.reply, nil
	}
	c.mu.Unlock()
	reply, err := c.upstream.Chat(ctx, request)
	if err != nil {
		return Reply{}, err
	}
	c.store(key, reply)
	return reply, nil
}

func (c *Cache) store(key [32]byte, reply Reply) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.entries[key] = entry{reply: reply, expires: time.Now().Add(c.ttl)}
}

// keyOf gives the key a request is kept under: a hash of the whole request as JSON, its model,
// every message and its options.
func keyOf(request ChatRequest) [32]byte {
	text, _ := json.Marshal(request)
	return sha256.Sum256(text)
}
