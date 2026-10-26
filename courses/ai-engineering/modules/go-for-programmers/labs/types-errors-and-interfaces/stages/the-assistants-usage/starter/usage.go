package gateway

import (
	"bufio"
	"cmp"
	"errors"
	"fmt"
	"io"
	"maps"
	"slices"
	"strconv"
	"strings"
)

// Usage counts each key's tokens by day, as the gateway charges them.
type Usage struct {
	tokens map[string]map[string]int // by key, then by day
	keys   []string                  // in the order they were first seen
}

var ErrOverLimit = errors.New("over the day's limit")

// NewUsage gives a count with nothing in it.
func NewUsage() *Usage {
	return &Usage{tokens: map[string]map[string]int{}}
}

// Add counts tokens for key on day, a date such as 2026-10-26.
func (u *Usage) Add(key, day string, tokens int) {
	if u.tokens[key] == nil {
		u.tokens[key] = map[string]int{}
		u.keys = append(u.keys, key)
	}
	u.tokens[key][day] += tokens
}

// Tokens gives key's tokens on day.
func (u *Usage) Tokens(key, day string) int {
	return u.tokens[key][day]
}

// Keys gives the keys in the order they were first seen.
func (u *Usage) Keys() []string {
	return u.keys
}

// Busiest gives the n keys with the most tokens on day, the most first.
func (u *Usage) Busiest(day string, n int) []string {
	keys := u.Keys()
	slices.SortStableFunc(keys, func(a, b string) int {
		return cmp.Compare(u.Tokens(b, day), u.Tokens(a, day))
	})
	return keys[:min(n, len(keys))]
}

// Merge adds other's counts, such as another of the gateway's servers kept.
func (u *Usage) Merge(other *Usage) {
	for key, days := range other.tokens {
		for day, tokens := range days {
			u.tokens[key][day] += tokens
		}
	}
}

// Charge counts tokens for key on day if they keep its day within limit, and refuses them with
// ErrOverLimit if not.
func (u *Usage) Charge(key, day string, tokens, limit int) error {
	if u.Tokens(key, day)+tokens > limit {
		return fmt.Errorf("key %s on %s: %w", key, day, ErrOverLimit)
	}
	u.Add(key, day, tokens)
	return nil
}

// A Use is a request's tokens, for a key on a day.
type Use struct {
	Key    string
	Day    string
	Tokens int
}

// ChargeAll charges each use in turn, and gives how many it refused for being over the limit.
func (u *Usage) ChargeAll(uses []Use, limit int) (int, error) {
	refused := 0
	for _, use := range uses {
		err := u.Charge(use.Key, use.Day, use.Tokens, limit)
		if err == ErrOverLimit {
			refused++
			continue
		}
		if err != nil {
			return refused, err
		}
	}
	return refused, nil
}

// Save writes the counts for LoadUsage to read: a line for each key and day, with its tokens.
func (u *Usage) Save(w io.Writer) error {
	for _, key := range u.keys {
		for _, day := range slices.Sorted(maps.Keys(u.tokens[key])) {
			if _, err := fmt.Fprintf(w, "%s %s %d\n", key, day, u.tokens[key][day]); err != nil {
				return err
			}
		}
	}
	return nil
}

// LoadUsage reads counts that Save wrote.
func LoadUsage(r io.Reader) (*Usage, error) {
	u := NewUsage()
	scanner := bufio.NewScanner(r)
	var err error
	for scanner.Scan() {
		key, day, tokens, err := parseLine(scanner.Text())
		if err != nil {
			break
		}
		u.Add(key, day, tokens)
	}
	if err != nil {
		return nil, err
	}
	return u, scanner.Err()
}

func parseLine(line string) (string, string, int, error) {
	fields := strings.Fields(line)
	if len(fields) != 3 {
		return "", "", 0, fmt.Errorf("usage line %q: want a key, a day and tokens", line)
	}
	tokens, err := strconv.Atoi(fields[2])
	if err != nil {
		return "", "", 0, fmt.Errorf("usage line %q: %w", line, err)
	}
	return fields[0], fields[1], tokens, nil
}
