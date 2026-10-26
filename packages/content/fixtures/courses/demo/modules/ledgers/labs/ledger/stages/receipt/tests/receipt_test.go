package tests

import (
	"slices"
	"testing"

	"example/ledger"
)

func TestReceipt(t *testing.T) {
	t.Run("tst_demo30 Shows each amount in dollars and cents", func(t *testing.T) {
		got := ledger.Receipt([]int{1250, 5})
		if len(got) < 2 || !slices.Equal(got[:2], []string{"12.50", "0.05"}) {
			t.Errorf("got %q, want the lines 12.50 and 0.05", got)
		}
	})
	t.Run("tst_demo31 Ends with the total", func(t *testing.T) {
		got := ledger.Receipt([]int{1250, 5})
		if len(got) == 0 || got[len(got)-1] != "Total 12.55" {
			t.Errorf("got %q, want it to end with Total 12.55", got)
		}
	})
}
