package checks

import (
	"testing"

	"example/gateway"
)

func TestChecks(t *testing.T) {
	t.Run("tst_eeeeee takes the first", func(t *testing.T) {
		if got := gateway.First([]int{3, 4}); got != 3 {
			t.Errorf("got %d, want 3", got)
		}
	})
}
