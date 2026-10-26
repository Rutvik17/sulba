package tests

import (
	"testing"
	"testing/synctest"
	"time"

	"example/totals"
)

func TestTotals(t *testing.T) {
	t.Run("tst_go0001 Adds the amounts", func(t *testing.T) {
		t.Log("Adding 2 amounts.")
		if got := totals.Sum([]int{1050, 500}); got != 1550 {
			t.Errorf("got %d, want 1550", got)
		}
	})
	t.Run("tst_go0002 Shows dollars and cents", func(t *testing.T) {
		if got := totals.Dollars(5); got != "0.05" {
			t.Errorf("got %q, want %q", got, "0.05")
		}
	})
	t.Run("tst_go0003 Waits a second for the till", func(t *testing.T) {
		synctest.Test(t, func(t *testing.T) {
			start := time.Now()
			if err := totals.Wait(false); err != nil || time.Since(start) != time.Second {
				t.Errorf("got %v after %v, want nil after 1s", err, time.Since(start))
			}
		})
	})
}
