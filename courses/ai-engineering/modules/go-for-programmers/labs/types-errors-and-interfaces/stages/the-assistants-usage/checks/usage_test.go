package checks

import (
	"slices"
	"strings"
	"testing"

	"example/gateway"
)

const today = "2026-10-26"

func TestUsageInUse(t *testing.T) {
	t.Run("tst_iqxtai Merges a key only the other server saw", func(t *testing.T) {
		defer func() {
			if stopped := recover(); stopped != nil {
				t.Errorf("Merge panicked: %v", stopped)
			}
		}()
		usage, other := gateway.NewUsage(), gateway.NewUsage()
		usage.Add("k1", today, 10)
		other.Add("k2", today, 50)
		usage.Merge(other)
		if got := usage.Tokens("k2", today); got != 50 {
			t.Errorf("got %d tokens for k2, want the other server's 50", got)
		}
		if got, want := usage.Keys(), []string{"k1", "k2"}; !slices.Equal(got, want) {
			t.Errorf("got the keys %q, want %q", got, want)
		}
	})
	t.Run("tst_e9f7dp Keeps the keys' order after a report of the busiest", func(t *testing.T) {
		usage := gateway.NewUsage()
		usage.Add("k1", today, 10)
		usage.Add("k2", today, 30)
		usage.Add("k3", today, 20)
		usage.Busiest(today, 2)
		if got, want := usage.Keys(), []string{"k1", "k2", "k3"}; !slices.Equal(got, want) {
			t.Errorf("after Busiest, got the keys %q, want %q", got, want)
		}
	})
	t.Run("tst_0ppk33 Counts a refusal and charges the rest", func(t *testing.T) {
		usage := gateway.NewUsage()
		refused, err := usage.ChargeAll([]gateway.Use{
			{Key: "k1", Day: today, Tokens: 60},
			{Key: "k1", Day: today, Tokens: 60},
			{Key: "k1", Day: today, Tokens: 30},
		}, 100)
		if refused != 1 || err != nil {
			t.Fatalf("got %d refused and the error %v, want 1 refused and no error", refused, err)
		}
		if got := usage.Tokens("k1", today); got != 90 {
			t.Errorf("got %d tokens, want 90 from the two uses within the limit", got)
		}
	})
	t.Run("tst_3vhuaj Gives an error for a line it can't read", func(t *testing.T) {
		usage, err := gateway.LoadUsage(strings.NewReader("k1 2026-10-26 120\nk2 2026-10-26 a-lot\nk3 2026-10-26 40\n"))
		if err == nil {
			t.Errorf("got no error, and %d tokens for k1, want an error for the second line", usage.Tokens("k1", today))
		}
	})
}
