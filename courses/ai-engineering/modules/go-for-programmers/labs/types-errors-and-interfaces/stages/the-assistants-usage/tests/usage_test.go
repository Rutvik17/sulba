package tests

import (
	"errors"
	"slices"
	"strings"
	"testing"

	"example/gateway"
)

const today = "2026-10-26"

func TestUsage(t *testing.T) {
	t.Run("tst_p18tem Counts each key's tokens by day", func(t *testing.T) {
		usage := gateway.NewUsage()
		usage.Add("k1", today, 120)
		usage.Add("k1", today, 30)
		usage.Add("k1", "2026-10-25", 40)
		usage.Add("k2", today, 5)
		if got := usage.Tokens("k1", today); got != 150 {
			t.Errorf("got %d tokens for k1 today, want 150", got)
		}
		if got := usage.Tokens("k1", "2026-10-25"); got != 40 {
			t.Errorf("got %d tokens for k1 yesterday, want 40", got)
		}
		if got := usage.Tokens("k3", today); got != 0 {
			t.Errorf("got %d tokens for a key never seen, want 0", got)
		}
	})
	t.Run("tst_9iedtb Lists the keys in the order they were first seen", func(t *testing.T) {
		usage := gateway.NewUsage()
		for _, key := range []string{"k2", "k1", "k2", "k3"} {
			usage.Add(key, today, 10)
		}
		if got, want := usage.Keys(), []string{"k2", "k1", "k3"}; !slices.Equal(got, want) {
			t.Errorf("got %q, want %q", got, want)
		}
	})
	t.Run("tst_airdre Gives the busiest keys of a day, the most first", func(t *testing.T) {
		usage := gateway.NewUsage()
		usage.Add("k1", today, 10)
		usage.Add("k2", today, 30)
		usage.Add("k3", today, 20)
		if got, want := usage.Busiest(today, 2), []string{"k2", "k3"}; !slices.Equal(got, want) {
			t.Errorf("got %q, want %q", got, want)
		}
		if got := usage.Busiest(today, 5); len(got) != 3 {
			t.Errorf("asked for 5 of 3 keys, got %q, want all 3", got)
		}
	})
	t.Run("tst_rlkvfe Refuses tokens over a day's limit with ErrOverLimit", func(t *testing.T) {
		usage := gateway.NewUsage()
		if err := usage.Charge("k1", today, 80, 100); err != nil {
			t.Fatalf("got the error %v, want none", err)
		}
		if err := usage.Charge("k1", today, 30, 100); !errors.Is(err, gateway.ErrOverLimit) {
			t.Fatalf("got the error %v, want ErrOverLimit", err)
		}
		if got := usage.Tokens("k1", today); got != 80 {
			t.Errorf("got %d tokens, want the 80 charged", got)
		}
	})
	t.Run("tst_4h9bpj Charges every use within the limit", func(t *testing.T) {
		usage := gateway.NewUsage()
		refused, err := usage.ChargeAll([]gateway.Use{
			{Key: "k1", Day: today, Tokens: 40},
			{Key: "k2", Day: today, Tokens: 90},
			{Key: "k1", Day: today, Tokens: 50},
		}, 100)
		if refused != 0 || err != nil {
			t.Fatalf("got %d refused and the error %v, want none", refused, err)
		}
		if usage.Tokens("k1", today) != 90 || usage.Tokens("k2", today) != 90 {
			t.Errorf("got %d and %d tokens, want 90 for each key", usage.Tokens("k1", today), usage.Tokens("k2", today))
		}
	})
	t.Run("tst_q1hi1y Adds another server's counts", func(t *testing.T) {
		usage, other := gateway.NewUsage(), gateway.NewUsage()
		usage.Add("k1", today, 10)
		other.Add("k1", today, 15)
		other.Add("k1", "2026-10-25", 5)
		usage.Merge(other)
		if usage.Tokens("k1", today) != 25 || usage.Tokens("k1", "2026-10-25") != 5 {
			t.Errorf("got %d and %d tokens, want 25 today and 5 yesterday", usage.Tokens("k1", today), usage.Tokens("k1", "2026-10-25"))
		}
	})
	t.Run("tst_ozu7fq Reads back what it saved", func(t *testing.T) {
		usage := gateway.NewUsage()
		usage.Add("k2", today, 7)
		usage.Add("k1", "2026-10-25", 40)
		usage.Add("k1", today, 3)
		var saved strings.Builder
		if err := usage.Save(&saved); err != nil {
			t.Fatalf("saving gave the error %v", err)
		}
		loaded, err := gateway.LoadUsage(strings.NewReader(saved.String()))
		if err != nil {
			t.Fatalf("loading gave the error %v", err)
		}
		if loaded.Tokens("k2", today) != 7 || loaded.Tokens("k1", "2026-10-25") != 40 || loaded.Tokens("k1", today) != 3 {
			t.Errorf("read back %q as different counts", saved.String())
		}
		if got, want := loaded.Keys(), []string{"k2", "k1"}; !slices.Equal(got, want) {
			t.Errorf("read back the keys %q, want %q", got, want)
		}
	})
}
